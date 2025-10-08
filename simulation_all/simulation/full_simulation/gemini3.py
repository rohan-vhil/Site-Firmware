import asyncio
import logging
import json
import math
import time
from pymodbus.server import ModbusTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    with open("installer_cfg.json") as f:
        installer_cfg = json.load(f)

    with open("modbus_registers.json") as f:
        register_defs = json.load(f)

    with open("control_register.json") as f:
        control_defs = json.load(f)
except FileNotFoundError as e:
    logger.error(f"Configuration file not found: {e}. Please ensure all JSON files are in the same directory.")
    exit()

GLOBAL_POWER_STATE = {
    "inverter_power": 0,
    "load_power": 0
}

def build_datablock(part_num):
    if part_num not in register_defs:
        raise ValueError(f"No register definition for part number: {part_num}")
    
    data_blocks = {}
    map_blocks = register_defs[part_num]["map"]
    for block_key, block in map_blocks.items():
        start = block["start_address"] - 1
        length = block["Length"]
        values = [0] * length
        data_blocks[block_key] = (ModbusSequentialDataBlock(start, values), start, length)
    return data_blocks

def generate_bell_curve_value(hour_fraction, peak=60000):
    mean = 0.5
    std_dev = 0.15
    return int(peak * math.exp(-((hour_fraction - mean) ** 2) / (2 * std_dev ** 2)))

def get_control_value(context, slave_id, ctrl_block, name, size=1):
    if not ctrl_block or name not in ctrl_block["data"]:
        return None
    
    meta = ctrl_block["data"][name]
    offset = meta["offset"]
    start_addr = ctrl_block["start_address"] - 1
    length = ctrl_block["Length"]
    
    try:
        regs = context[slave_id].getValues(3, start_addr, length)
        if offset + size > len(regs):
            return None
        if size == 2:
            return (regs[offset] << 16) + regs[offset + 1]
        return regs[offset]
    except Exception as e:
        logger.warning(f"Error reading control value '{name}': {e}")
        return None

async def update_dynamic_values(context, slave_id, part_num, role=None):
    if part_num not in register_defs or "map" not in register_defs[part_num]:
        logger.warning(f"No data map for device {part_num}, updater will not run.")
        return

    reg_blocks = register_defs[part_num]["map"]
    rated_power = next((d.get("rated_power", 60000) for d in installer_cfg["device_list"] if d["part_num"] == part_num), 60000)
    ctrl_block = control_defs.get(part_num, {}).get("block1")

    while True:
        now = time.localtime()
        hour = now.tm_hour + now.tm_min / 60.0
        hour_frac = (now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec) / 86400.0

        for block_name, block in reg_blocks.items():
            if "data" not in block:
                continue

            data_map = block["data"]
            start_addr = block["start_address"] - 1
            length = block["Length"]
            
            try:
                regs = list(context[slave_id].getValues(3, start_addr, length))

                for name, meta in data_map.items():
                    offset = meta["offset"]
                    if offset >= len(regs):
                        continue

                    if name == "total_power":
                        if role == "load_meter":
                            load_val = 60000 if 7 <= hour < 18 else 0
                            if 15 <= hour < 15.5:
                                load_val = int(0.5 * load_val)
                            regs[offset] = load_val
                            GLOBAL_POWER_STATE["load_power"] = load_val

                        elif role == "grid_meter":
                            inv = GLOBAL_POWER_STATE.get("inverter_power", 0)
                            load = GLOBAL_POWER_STATE.get("load_power", 0)
                            grid_val = max(0, load - inv)
                            regs[offset] = grid_val

                        else:
                            inv_val = generate_bell_curve_value(hour_frac, rated_power)
                            if ctrl_block:
                                en = get_control_value(context, slave_id, ctrl_block, "power_limit_en")
                                if en == 1:
                                    inc = get_control_value(context, slave_id, ctrl_block, "increase_power", 2)
                                    dec = get_control_value(context, slave_id, ctrl_block, "decrease_power", 2)
                                    if inc and inc > 0:
                                        inv_val = int(inc)
                                    elif dec and dec > 0:
                                        inv_val = max(0, rated_power - int(dec))
                            regs[offset] = inv_val
                            GLOBAL_POWER_STATE["inverter_power"] = inv_val

                    elif name.startswith("L") and "voltage" in name:
                        regs[offset] = int(230 + 5 * math.sin(2 * math.pi * hour_frac))
                    elif name == "acfreq":
                        regs[offset] = int(499 + 2 * math.sin(2 * math.pi * hour_frac))

                context[slave_id].setValues(3, start_addr, regs)

            except Exception as e:
                logger.error(f"Error updating values for {part_num} (role: {role}): {e}")

        await asyncio.sleep(5)

async def launch_device(device):
    part_num = device["part_num"]
    ip = device["modbus_tcp_details"]["IP"]
    port = int(device["modbus_tcp_details"]["port"])
    slave_id = int(device["modbus_tcp_details"]["slave_id"])
    role = device.get("role")

    logger.info(f"[{part_num} - {role}] Starting Modbus TCP server on {ip}:{port} with slave ID {slave_id}")
    
    server = None
    try:
        block_map = build_datablock(part_num)
        store = ModbusSlaveContext()
        for _, (db, start, _) in block_map.items():
            store.setValues(3, start, db.values)

        context = ModbusServerContext(slaves={slave_id: store}, single=False)

        identity = ModbusDeviceIdentification()
        identity.VendorName = "SimCorp"
        identity.ProductCode = part_num
        identity.VendorUrl = "http://enercog.com/"
        identity.ProductName = f"{part_num} Simulator"
        identity.ModelName = "VirtualDevice"
        identity.MajorMinorRevision = "1.0"

        # Create the data update task
        asyncio.create_task(update_dynamic_values(context, slave_id, part_num, role))
        
        # Create and run the server
        server = ModbusTcpServer(context, identity=identity, address=(ip, port))
        await server.serve_forever()

    except asyncio.CancelledError:
        logger.info(f"[{part_num} - {role}] Server cancelled.")
        
    except Exception as e:
        logger.error(f"Failed to launch device {part_num}: {e}")
        
    finally:
        if server:
            logger.info(f"[{part_num} - {role}] Shutting down server...")
            await server.shutdown()

async def main():
    site_id = installer_cfg.get("site id", "NO_SITE")
    devices = installer_cfg.get("device_list", [])
    logger.info(f"Installing site: {site_id}")
    
    tasks = [launch_device(dev) for dev in devices]
    if not tasks:
        logger.warning("No devices found in installer_cfg.json. Exiting.")
        return
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Simulation shutdown initiated by user.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Simulation stopped by user.")
