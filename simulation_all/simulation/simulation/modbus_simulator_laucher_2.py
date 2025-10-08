import asyncio
import logging
import json
import math
import time
from pymodbus.server.async_io import StartAsyncTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load config files
with open("installer_cfg.json") as f:
    installer_cfg = json.load(f)

with open("modbus_registers.json") as f:
    register_defs = json.load(f)

# Global dict to track simulation state
simulated_values = {}


def build_datablock(part_num, register_defs):
    if part_num not in register_defs:
        raise ValueError(f"No register definition found for part number: {part_num}")

    device_map = register_defs[part_num]["map"]
    for block_key, block in device_map.items():
        start_address = block.get("start_address", 0)
        length = block.get("Length", 0)
        if length <= 0:
            continue

        registers = [0] * length
        for name, meta in block["data"].items():
            offset = meta["offset"]
            if offset < length:
                value = 0
                registers[offset] = value

        datablock = ModbusSequentialDataBlock(start_address, registers)
        return datablock, start_address, block_key

    raise ValueError("No valid register blocks found.")


def generate_bell_curve_value(hour_fraction, peak=10000):
    """
    Returns value between 0 to `peak` based on time of day using bell curve.
    hour_fraction: float between 0.0 (midnight) and 1.0 (just before next midnight)
    """
    # Peak generation around solar noon (0.5), standard deviation defines spread
    mean = 0.5
    std_dev = 0.15
    value = peak * math.exp(-((hour_fraction - mean) ** 2) / (2 * std_dev ** 2))
    return int(value)


async def update_dynamic_values(context, slave_id, part_num):
    block_info = register_defs[part_num]["map"]
    block_key = list(block_info.keys())[0]
    block = block_info[block_key]
    start_addr = block["start_address"]
    data_map = block["data"]

    while True:
        current_time = time.localtime()
        hour_fraction = (current_time.tm_hour * 3600 + current_time.tm_min * 60 + current_time.tm_sec) / 86400

        values = [0] * block["Length"]

        for key, meta in data_map.items():
            offset = meta["offset"]
            scale = meta.get("scale", 1.0)

            if key == "total_power":
                val = generate_bell_curve_value(hour_fraction, peak=10000) * scale
            elif key == "acfreq":
                val = int(499 + 2 * math.sin(2 * math.pi * hour_fraction))  # simulate 49.9Hz to 50.1Hz
            else:
                val = int(230 + 5 * math.sin(2 * math.pi * hour_fraction))  # simulate 230V +/- 5V

            values[offset] = int(val)

        context[slave_id].setValues(3, start_addr, values)
        await asyncio.sleep(5)


async def launch_device(device, register_defs):
    part_num = device["part_num"]
    ip = device["modbus_tcp_details"]["IP"]
    port = int(device["modbus_tcp_details"]["port"])
    slave_id = int(device["modbus_tcp_details"]["slave_id"])

    logger.info(f"[{part_num}] Starting Modbus TCP server on {ip}:{port}")

    block, start_addr, _ = build_datablock(part_num, register_defs)
    store = ModbusSlaveContext(hr=block)
    context = ModbusServerContext(slaves={slave_id: store}, single=False)

    identity = ModbusDeviceIdentification()
    identity.VendorName = "Simulator Inc."
    identity.ProductCode = part_num
    identity.VendorUrl = "https://example.com"
    identity.ProductName = part_num
    identity.ModelName = "VirtualModel"
    identity.MajorMinorRevision = "1.0"

    asyncio.create_task(update_dynamic_values(context, slave_id, part_num))

    await StartAsyncTcpServer(context, identity=identity, address=(ip, port))


async def main():
    site_id = installer_cfg.get("site id", "UNKNOWN_SITE")
    device_list = installer_cfg.get("device_list", [])

    logger.info(f"Installing site: {site_id}, devices: {len(device_list)}")

    tasks = []
    for device in device_list:
        tasks.append(launch_device(device, register_defs))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
