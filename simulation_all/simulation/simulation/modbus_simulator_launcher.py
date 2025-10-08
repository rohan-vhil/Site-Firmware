# # # # import asyncio
# # # # import json
# # # # import random
# # # # from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
# # # # from pymodbus.server.async_io import StartAsyncTcpServer


# # # # def load_json_file(path):
# # # #     with open(path, "r") as f:
# # # #         return json.load(f)


# # # # def build_datablock(start_address, register_defs):
# # # #     max_offset = max(v["offset"] + v["size"] for v in register_defs.values())
# # # #     return ModbusSequentialDataBlock(start_address, [0] * max_offset)


# # # # async def update_loop(context, start_address, data_defs, part_num):
# # # #     while True:
# # # #         for name, meta in data_defs.items():
# # # #             offset = meta["offset"]
# # # #             value = {
# # # #                 "L1_voltage": random.randint(2200, 2400),
# # # #                 "L2_voltage": random.randint(2200, 2400),
# # # #                 "L3_voltage": random.randint(2200, 2400),
# # # #                 "total_power": random.randint(1000, 10000),
# # # #                 "acfreq": random.randint(495, 505)
# # # #             }.get(name, random.randint(0, 1000))
# # # #             context.setValues(3, start_address + offset, [value])
# # # #         await asyncio.sleep(2)


# # # # async def launch_device(device, register_map):
# # # #     part_num = device["part_num"]
# # # #     ip = device["modbus_tcp_details"]["IP"]
# # # #     port = int(device["modbus_tcp_details"]["port"])
# # # #     slave_id = int(device["modbus_tcp_details"]["slave_id"])

# # # #     registers = register_map.get(part_num, {})
# # # #     if not registers:
# # # #         print(f"[ERROR] No register map for {part_num}")
# # # #         return

# # # #     for block_name, block in registers.items():
# # # #         start_addr = block["start_address"]
# # # #         data_defs = block["data"]

# # # #         data_block = build_datablock(start_addr, data_defs)
# # # #         slave_context = ModbusSlaveContext(hr=data_block)
# # # #         server_context = ModbusServerContext(slaves={slave_id: slave_context}, single=False)
# # # #         server_context.zero_mode = True

# # # #         print(f"[{part_num}] Starting Modbus TCP server on {ip}:{port}")

# # # #         # Background data updater
# # # #         asyncio.create_task(update_loop(slave_context, start_addr, data_defs, part_num))

# # # #         # Start Modbus server (✅ no 'allow_reuse_address')
# # # #         asyncio.create_task(StartAsyncTcpServer(
# # # #             context=server_context,
# # # #             address=(ip, port)
# # # #         ))


# # # # async def main():
# # # #     installer_cfg = load_json_file("installer_cfg.json")
# # # #     register_defs = load_json_file("modbus_registers.json")

# # # #     for device in installer_cfg["device_list"]:
# # # #         if device["comm_type"] == "modbus-tcp":
# # # #             await launch_device(device, register_defs)

# # # #     print("✅ All Modbus TCP devices launched. Waiting for client connections...")
# # # #     while True:
# # # #         await asyncio.sleep(60)


# # # # if __name__ == "__main__":
# # # #     try:
# # # #         asyncio.run(main())
# # # #     except KeyboardInterrupt:
# # # #         print("\n🛑 Simulator stopped.")


# # # import asyncio
# # # import json
# # # from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
# # # from pymodbus.server import async_io
# # # import random

# # # # ------------------ Load Configs ------------------
# # # with open("installer_cfg.json") as f:
# # #     installer_config = json.load(f)

# # # with open("modbus_registers.json") as f:
# # #     register_definitions = json.load(f)

# # # # ------------------ Helpers ------------------
# # # def build_datablock(device_partnum, register_map):
# # #     block = register_map[device_partnum]['block1']
# # #     start_address = block['start_address']
# # #     total_length = block['Length']

# # #     values = [random.randint(200, 240) for _ in range(total_length)]  # Simulated values
# # #     datablock = ModbusSequentialDataBlock(start_address, values)
# # #     return datablock, start_address

# # # async def launch_device(device):
# # #     part_num = device['part_num']
# # #     ip = device['modbus_tcp_details']['IP']
# # #     port = int(device['modbus_tcp_details']['port'])

# # #     if part_num not in register_definitions:
# # #         print(f"❌ No register definition for {part_num}")
# # #         return

# # #     # Build holding register block
# # #     block = register_definitions[part_num]['block1']
# # #     datablock, start_address = build_datablock(part_num, register_definitions)

# # #     slave_context = ModbusSlaveContext(hr=datablock)
# # #     context = ModbusServerContext(slaves={1: slave_context}, single=False)

# # #     print(f"[{part_num}] Starting Modbus TCP server on {ip}:{port}")

# # #     # await async_io.StartAsyncTcpServer(
# # #     #     context,
# # #     #     address=(ip, port),
# # #     #     defer_start=False,
# # #     # )

# # #     await async_io.StartAsyncTcpServer(
# # #     context=slave_context,
# # #     #identity=identity,
# # #     address=(ip, port)
# # #     )


# # # async def main():
# # #     devices = installer_config['device_list']
# # #     print(f"Installing site: {installer_config.get('site id')}, devices: {len(devices)}")

# # #     tasks = []
# # #     for device in devices:
# # #         if device['comm_type'] == 'modbus-tcp':
# # #             tasks.append(asyncio.create_task(launch_device(device)))

# # #     await asyncio.gather(*tasks)

# # # if __name__ == "__main__":
# # #     asyncio.run(main())

# # import asyncio
# # import json
# # from pymodbus.server.async_io import StartAsyncTcpServer
# # from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext
# # from pymodbus.datastore.store import ModbusSequentialDataBlock
# # from pymodbus.device import ModbusDeviceIdentification

# # # Load installer config and register map
# # with open("installer_cfg.json") as f:
# #     installer_config = json.load(f)

# # with open("modbus_registers.json") as f:
# #     register_definitions = json.load(f)

# # site_id = installer_config.get("site id")
# # devices = installer_config.get("device_list", [])
# # print(f"Installing site: {site_id}, devices: {len(devices)}")


# # def build_datablock(part_num, reg_def):
# #     block = reg_def[part_num]["block1"]
# #     start_address = block["start_address"]
# #     data = block["data"]
# #     total_length = max([v["offset"] + v["size"] for v in data.values()])
# #     block_data = [0] * total_length
# #     return ModbusSequentialDataBlock(start_address, block_data), start_address


# # async def launch_device(device, reg_def):
# #     part_num = device["part_num"]
# #     ip = device["modbus_tcp_details"]["IP"]
# #     port = int(device["modbus_tcp_details"]["port"])
# #     slave_id = int(device["modbus_tcp_details"].get("slave_id", 1))

# #     datablock, _ = build_datablock(part_num, reg_def)
# #     slave_context = ModbusSlaveContext(hr=datablock)
# #     server_context = ModbusServerContext(slaves={slave_id: slave_context}, single=False)

# #     identity = ModbusDeviceIdentification()
# #     identity.VendorName = "Enercog"
# #     identity.ProductCode = part_num
# #     identity.VendorUrl = "https://app.enercog.com"
# #     identity.ProductName = f"{part_num} Modbus Simulator"
# #     identity.ModelName = "ModbusSim v1"
# #     identity.MajorMinorRevision = "1.0"

# #     print(f"[{part_num}] Starting Modbus TCP server on {ip}:{port}")

# #     await StartAsyncTcpServer(
# #         context=server_context,
# #         identity=identity,
# #         address=(ip, port)
# #     )


# # async def main():
# #     tasks = []
# #     for device in devices:
# #         if device["comm_type"].lower() == "modbus-tcp":
# #             tasks.append(asyncio.create_task(launch_device(device, register_definitions)))

# #     print("\u2705 All Modbus TCP devices launched. Waiting for client connections...")
# #     await asyncio.gather(*tasks)


# # if __name__ == "__main__":
# #     asyncio.run(main())


# import asyncio
# import json
# import logging
# from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext, ModbusSequentialDataBlock
# from pymodbus.device import ModbusDeviceIdentification
# from pymodbus.server.async_io import StartAsyncTcpServer
# from pathlib import Path

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# CONFIG_PATH = Path("installer_cfg.json")
# REGISTERS_PATH = Path("modbus_registers.json")


# def load_config():
#     with open(CONFIG_PATH) as f:
#         config = json.load(f)
#     with open(REGISTERS_PATH) as f:
#         register_definitions = json.load(f)
#     return config, register_definitions


# def build_datablock(part_num, register_definitions):
#     definition = register_definitions.get(part_num)
#     if not definition:
#         raise ValueError(f"No register definition found for {part_num}")

#     blocks = definition.get("map", {})
#     all_blocks = {}

#     for block_name, block in blocks.items():
#         start_address = block["start_address"]
#         length = block.get("Length")
#         if not length:
#             data_points = block["data"]
#             max_end = max(dp["offset"] + dp["size"] for dp in data_points.values())
#             length = max_end
#         values = [0] * length
#         all_blocks[start_address] = values
#         logger.info(f"➡️ Register block '{block_name}' @ {start_address} → {length} registers")

#     if not all_blocks:
#         raise ValueError("No valid register blocks found.")

#     min_addr = min(all_blocks.keys())
#     max_addr = max(addr + len(vals) for addr, vals in all_blocks.items())
#     full_block = [0] * (max_addr - min_addr)

#     for addr, vals in all_blocks.items():
#         offset = addr - min_addr
#         full_block[offset:offset+len(vals)] = vals

#     datablock = ModbusSequentialDataBlock(min_addr, full_block)
#     return datablock, min_addr


# async def launch_device(device, register_definitions):
#     part_num = device["part_num"]
#     port = int(device["modbus_tcp_details"]["port"])
#     ip = device["modbus_tcp_details"].get("ip", "127.0.0.1")
#     slave_id = 0  # You can adjust this if needed

#     logger.info(f"[{part_num}] Starting Modbus TCP server on {ip}:{port}")
#     datablock, start_address = build_datablock(part_num, register_definitions)

#     store = ModbusSlaveContext(hr=datablock)
#     context = ModbusServerContext(slaves={slave_id: store}, single=False)

#     identity = ModbusDeviceIdentification()
#     identity.VendorName = part_num
#     identity.ProductCode = "PY"
#     identity.VendorUrl = "https://example.com"
#     identity.ProductName = f"ModbusSim_{part_num}"
#     identity.ModelName = "ModbusSim"
#     identity.MajorMinorRevision = "1.0"

#     await StartAsyncTcpServer(
#         context,
#         identity=identity,
#         address=(ip, port)
#     )


# async def main():
#     config, register_definitions = load_config()
#     devices = config.get("project_devices", [])
#     site = config.get("site_id", "SIM_SITE_001")

#     logger.info(f"Installing site: {site}, devices: {len(devices)}")
#     tasks = [launch_device(device, register_definitions) for device in devices]
#     await asyncio.gather(*tasks)


# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         print("\nSimulation stopped by user.")

#




# import asyncio
# import logging
# import json
# from pymodbus.server.async_io import StartAsyncTcpServer
# from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
# from pymodbus.device import ModbusDeviceIdentification

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Load config files
# with open("installer_cfg.json") as f:
#     installer_cfg = json.load(f)

# with open("modbus_registers.json") as f:
#     register_defs = json.load(f)

# def build_datablock(part_num, register_defs):
#     """
#     Builds a ModbusSequentialDataBlock for the given part number,
#     filling it with predefined values based on the offset.
#     """
#     if part_num not in register_defs:
#         raise ValueError(f"No register definition found for part number: {part_num}")

#     device_map = register_defs[part_num]["map"]
#     for block_key, block in device_map.items():
#         start_address = block.get("start_address", 0)
#         length = block.get("Length", 0)
#         if length <= 0:
#             continue

#         registers = [0] * length
#         for name, meta in block["data"].items():
#             offset = meta["offset"]
#             value = 0
#             # Simulated default values
#             if "voltage" in name:
#                 value = 230
#             elif "acfreq" in name:
#                 value = 50
#             elif "total_power" in name:
#                 value = 3000

#             if offset < length:
#                 registers[offset] = value
#         datablock = ModbusSequentialDataBlock(start_address, registers)
#         return datablock, start_address

#     raise ValueError("No valid register blocks found.")

# async def launch_device(device, register_defs):
#     part_num = device["part_num"]
#     ip = device["modbus_tcp_details"]["IP"]
#     port = int(device["modbus_tcp_details"]["port"])
#     slave_id = int(device["modbus_tcp_details"]["slave_id"])

#     logger.info(f"[{part_num}] Starting Modbus TCP server on {ip}:{port}")

#     block, _ = build_datablock(part_num, register_defs)
#     store = ModbusSlaveContext(hr=block)
#     context = ModbusServerContext(slaves={slave_id: store}, single=False)

#     identity = ModbusDeviceIdentification()
#     identity.VendorName = "Simulator Inc."
#     identity.ProductCode = part_num
#     identity.VendorUrl = "https://example.com"
#     identity.ProductName = part_num
#     identity.ModelName = "VirtualModel"
#     identity.MajorMinorRevision = "1.0"

#     await StartAsyncTcpServer(context, identity=identity, address=(ip, port))

# async def main():
#     site_id = installer_cfg.get("site id", "UNKNOWN_SITE")
#     device_list = installer_cfg.get("device_list", [])

#     logger.info(f"Installing site: {site_id}, devices: {len(device_list)}")

#     tasks = []
#     for device in device_list:
#         tasks.append(launch_device(device, register_defs))

#     await asyncio.gather(*tasks)

# if __name__ == "__main__":
#     asyncio.run(main())




import asyncio
import logging
import json
from pymodbus.server.async_io import StartAsyncTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Predefined values for registers by name
PREDEFINED_VALUES = {
    "L1_voltage": 230,
    "L2_voltage": 231,
    "L3_voltage": 229,
    "total_power": 5000,
    "acfreq": 50
}

# Load config files
with open("installer_cfg.json") as f:
    installer_cfg = json.load(f)

with open("modbus_registers.json") as f:
    register_defs = json.load(f)

def build_datablock(part_num, register_defs):
    if part_num not in register_defs:
        raise ValueError(f"No register definition found for part number: {part_num}")

    device_map = register_defs[part_num]["map"]
    for block in device_map.values():
        logical_start_address = block.get("start_address", 0)
        length = block.get("Length", 0)

        if length <= 0:
            continue

        registers = [0] * length
        for name, meta in block["data"].items():
            offset = meta["offset"]
            if offset < length:
                value = PREDEFINED_VALUES.get(name, 0)
                registers[offset] = value

        # Important: simulate register block starting from actual logical address
        datablock = ModbusSequentialDataBlock(logical_start_address, registers)
        return datablock, logical_start_address

    raise ValueError("No valid register blocks found.")

async def launch_device(device, register_defs):
    part_num = device["part_num"]
    ip = device["modbus_tcp_details"]["IP"]
    port = int(device["modbus_tcp_details"]["port"])
    slave_id = int(device["modbus_tcp_details"]["slave_id"])

    logger.info(f"[{part_num}] Starting Modbus TCP server on {ip}:{port}")

    block, _ = build_datablock(part_num, register_defs)
    store = ModbusSlaveContext(hr=block)
    context = ModbusServerContext(slaves={slave_id: store}, single=False)

    identity = ModbusDeviceIdentification()
    identity.VendorName = "Simulator Inc."
    identity.ProductCode = part_num
    identity.VendorUrl = "https://example.com"
    identity.ProductName = part_num
    identity.ModelName = "VirtualModel"
    identity.MajorMinorRevision = "1.0"

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



