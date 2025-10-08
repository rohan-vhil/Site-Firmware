# # # import asyncio
# # # import logging
# # # import json
# # # import math
# # # import time
# # # from pymodbus.server.async_io import StartAsyncTcpServer
# # # from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
# # # from pymodbus.device import ModbusDeviceIdentification

# # # logging.basicConfig(level=logging.INFO)
# # # logger = logging.getLogger(__name__)

# # # with open("installer_cfg.json") as f:
# # #     installer_cfg = json.load(f)

# # # with open("modbus_registers.json") as f:
# # #     register_defs = json.load(f)

# # # with open("control_register.json") as f:
# # #     control_defs = json.load(f)

# # # def build_datablock(part_num):
# # #     if part_num not in register_defs:
# # #         raise ValueError(f"No register definition for part number: {part_num}")
# # #     data_blocks = {}
# # #     map_blocks = register_defs[part_num]["map"]
# # #     for block_key, block in map_blocks.items():
# # #         start = block["start_address"] - 1  # zero-based
# # #         length = block["Length"]
# # #         values = [0] * length
# # #         data_blocks[block_key] = (ModbusSequentialDataBlock(start, values), start, length)
# # #     return data_blocks

# # # def generate_bell_curve_value(hour_fraction, peak=60000):
# # #     mean = 0.5
# # #     std_dev = 0.15
# # #     return int(peak * math.exp(-((hour_fraction - mean) ** 2) / (2 * std_dev ** 2)))

# # # def get_control_value(context, slave_id, ctrl_block, name, size=1):
# # #     if name not in ctrl_block["data"]:
# # #         return None
# # #     meta = ctrl_block["data"][name]
# # #     offset = meta["offset"]
# # #     start_addr = ctrl_block["start_address"] - 1  # zero-based
# # #     length = ctrl_block["Length"]
# # #     regs = context[slave_id].getValues(3, start_addr, length)
# # #     if offset + size > len(regs):
# # #         return None
# # #     if size == 2:
# # #         return (regs[offset] << 16) + regs[offset + 1]
# # #     return regs[offset]

# # # async def update_dynamic_values(context, slave_id, part_num, role=None):
# # #     if part_num not in register_defs or "map" not in register_defs[part_num]:
# # #         logger.warning(f"No data map for device {part_num}")
# # #         return

# # #     reg_blocks = register_defs[part_num]["map"]
# # #     rated_power = 60000
# # #     for d in installer_cfg["device_list"]:
# # #         if d["part_num"] == part_num and "rated_power" in d:
# # #             rated_power = int(d["rated_power"])
# # #             break

# # #     ctrl_block = control_defs.get(part_num, {}).get("block1")

# # #     while True:
# # #         now = time.localtime()
# # #         hour = now.tm_hour + now.tm_min / 60
# # #         hour_frac = (now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec) / 86400

# # #         inverter_power = 0
# # #         load_power = 0

# # #         for dev in installer_cfg["device_list"]:
# # #             if dev["part_num"] == "GROWATT123":
# # #                 inv_slave = int(dev["modbus_tcp_details"]["slave_id"])
# # #                 try:
# # #                     inv_start = register_defs["GROWATT123"]["map"]["block1"]["start_address"] - 1
# # #                     inv_regs = context[inv_slave].getValues(3, inv_start, 10)
# # #                     inverter_power = inv_regs[3]
# # #                 except Exception as e:
# # #                     logger.warning(f"Failed to read inverter power: {e}")

# # #         for dev in installer_cfg["device_list"]:
# # #             if dev["part_num"] == "UMG104":
# # #                 load_slave = int(dev["modbus_tcp_details"]["slave_id"])
# # #                 try:
# # #                     load_start = register_defs["UMG104"]["map"]["block1"]["start_address"] - 1
# # #                     load_regs = context[load_slave].getValues(3, load_start, 10)
# # #                     load_power = load_regs[3]
# # #                 except Exception as e:
# # #                     logger.warning(f"Failed to read load power: {e}")

# # #         for block_name, block in reg_blocks.items():
# # #             if "data" not in block:
# # #                 continue

# # #             data_map = block["data"]
# # #             start_addr = block["start_address"] - 1  # zero-based
# # #             length = block["Length"]
# # #             regs = list(context[slave_id].getValues(3, start_addr, length))

# # #             for name, meta in data_map.items():
# # #                 offset = meta["offset"]
# # #                 if name == "total_power":
# # #                     if role == "load_meter":
# # #                         if 7 <= hour < 18:
# # #                             power = 80000
# # #                             if 15 <= hour < 15.5:
# # #                                 power = int(0.5 * power)
# # #                         else:
# # #                             power = 10000
# # #                         regs[offset] = power

# # #                     elif role == "grid_meter":
# # #                         power = max(0, load_power - inverter_power)
# # #                         regs[offset] = power

# # #                     else:  # inverter
# # #                         power = generate_bell_curve_value(hour_frac, rated_power)
# # #                         if ctrl_block:
# # #                             en = get_control_value(context, slave_id, ctrl_block, "power_limit_en")
# # #                             if en == 1:
# # #                                 inc = get_control_value(context, slave_id, ctrl_block, "increase_power", size=2)
# # #                                 dec = get_control_value(context, slave_id, ctrl_block, "decrease_power", size=2)
# # #                                 if inc is not None and inc > 0:
# # #                                     power = int(inc)
# # #                                 elif dec is not None and dec > 0:
# # #                                     power = max(0, rated_power - int(dec))
# # #                         regs[offset] = power

# # #                 elif name.startswith("L") and "voltage" in name:
# # #                     regs[offset] = int(230 + 5 * math.sin(2 * math.pi * hour_frac))

# # #                 elif name == "acfreq":
# # #                     regs[offset] = int(499 + 2 * math.sin(2 * math.pi * hour_frac))

# # #             context[slave_id].setValues(3, start_addr, regs)

# # #         await asyncio.sleep(5)

# # # async def launch_device(device):
# # #     part_num = device["part_num"]
# # #     ip = device["modbus_tcp_details"]["IP"]
# # #     port = int(device["modbus_tcp_details"]["port"])
# # #     slave_id = int(device["modbus_tcp_details"]["slave_id"])
# # #     role = device.get("role")

# # #     logger.info(f"[{part_num} - {role}] Starting Modbus TCP server on {ip}:{port}")

# # #     block_map = build_datablock(part_num)
# # #     store = ModbusSlaveContext()
# # #     for _, (db, start, _) in block_map.items():
# # #         store.setValues(3, start, db.values)

# # #     context = ModbusServerContext(slaves={slave_id: store}, single=False)

# # #     identity = ModbusDeviceIdentification()
# # #     identity.VendorName = "SimCorp"
# # #     identity.ProductCode = part_num
# # #     identity.ProductName = part_num
# # #     identity.ModelName = "VirtualDevice"
# # #     identity.MajorMinorRevision = "1.0"

# # #     asyncio.create_task(update_dynamic_values(context, slave_id, part_num, role))
# # #     await StartAsyncTcpServer(context, identity=identity, address=(ip, port))

# # # async def main():
# # #     site_id = installer_cfg.get("site id", "NO_SITE")
# # #     devices = installer_cfg.get("device_list", [])
# # #     logger.info(f"Installing site: {site_id}")
# # #     tasks = [launch_device(dev) for dev in devices]
# # #     await asyncio.gather(*tasks)

# # # if __name__ == "__main__":
# # #     asyncio.run(main())

# # import asyncio
# # import logging
# # import json
# # import math
# # import time
# # from pymodbus.server.async_io import StartAsyncTcpServer
# # from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
# # from pymodbus.device import ModbusDeviceIdentification

# # logging.basicConfig(level=logging.INFO)
# # logger = logging.getLogger(__name__)

# # with open("installer_cfg.json") as f:
# #     installer_cfg = json.load(f)

# # with open("modbus_registers.json") as f:
# #     register_defs = json.load(f)

# # with open("control_register.json") as f:
# #     control_defs = json.load(f)

# # GLOBAL_CONTEXTS = {}  # {part_num: (context, slave_id)}

# # def build_datablock(part_num):
# #     if part_num not in register_defs:
# #         raise ValueError(f"No register definition for part number: {part_num}")
# #     data_blocks = {}
# #     map_blocks = register_defs[part_num]["map"]
# #     for block_key, block in map_blocks.items():
# #         start = block["start_address"] - 1
# #         length = block["Length"]
# #         values = [0] * length
# #         data_blocks[block_key] = (ModbusSequentialDataBlock(start, values), start, length)
# #     return data_blocks

# # def generate_bell_curve_value(hour_fraction, peak=60000):
# #     mean = 0.5
# #     std_dev = 0.15
# #     return int(peak * math.exp(-((hour_fraction - mean) ** 2) / (2 * std_dev ** 2)))

# # def get_control_value(context, slave_id, ctrl_block, name, size=1):
# #     if name not in ctrl_block["data"]:
# #         return None
# #     meta = ctrl_block["data"][name]
# #     offset = meta["offset"]
# #     start_addr = ctrl_block["start_address"] - 1
# #     length = ctrl_block["Length"]
# #     regs = context[slave_id].getValues(3, start_addr, length)
# #     if offset + size > len(regs):
# #         return None
# #     if size == 2:
# #         return (regs[offset] << 16) + regs[offset + 1]
# #     return regs[offset]

# # def safe_read(part_num, block_key, offset):
# #     try:
# #         context, slave_id = GLOBAL_CONTEXTS[part_num]
# #         block = register_defs[part_num]["map"][block_key]
# #         start_addr = block["start_address"] - 1
# #         length = block["Length"]
# #         regs = context[slave_id].getValues(3, start_addr, length)
# #         return regs[offset]
# #     except Exception as e:
# #         logger.warning(f"Failed to read {part_num}: {e}")
# #         return 0

# # async def update_dynamic_values(context, slave_id, part_num, role=None):
# #     if part_num not in register_defs or "map" not in register_defs[part_num]:
# #         logger.warning(f"No data map for device {part_num}")
# #         return

# #     reg_blocks = register_defs[part_num]["map"]
# #     rated_power = 60000
# #     for d in installer_cfg["device_list"]:
# #         if d["part_num"] == part_num and "rated_power" in d:
# #             rated_power = int(d["rated_power"])
# #             break

# #     ctrl_block = control_defs.get(part_num, {}).get("block1")

# #     while True:
# #         now = time.localtime()
# #         hour = now.tm_hour + now.tm_min / 60
# #         hour_frac = (now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec) / 86400

# #         inverter_power = safe_read("GROWATT123", "block1", 3)
# #         load_power = safe_read("UMG104", "block1", 3)

# #         for block_name, block in reg_blocks.items():
# #             if "data" not in block:
# #                 continue

# #             data_map = block["data"]
# #             start_addr = block["start_address"] -1
# #             length = block["Length"]
# #             regs = list(context[slave_id].getValues(3, start_addr, length)) 

# #             for name, meta in data_map.items():
# #                 offset = meta["offset"]
# #                 if name == "total_power":
# #                     if role == "load_meter":
# #                         if 7 <= hour < 18:
# #                             power = 80000
# #                             print("___Inside load---",power)
# #                             if 15 <= hour < 15.5:
# #                                 power = int(0.5 * power)
# #                         else:
# #                             power = 10000
# #                         regs[offset] = power
# #                         print(regs[offset])
# #                     elif role == "grid_meter":
# #                         power = max(0, load_power - inverter_power)
# #                         regs[offset] = power
# #                         print("___Inside Grid---",power)

# #                     else:
# #                         power = generate_bell_curve_value(hour_frac, rated_power)
# #                         if ctrl_block:
# #                             en = get_control_value(context, slave_id, ctrl_block, "power_limit_en")
# #                             if en == 1:
# #                                 inc = get_control_value(context, slave_id, ctrl_block, "increase_power", 2)
# #                                 dec = get_control_value(context, slave_id, ctrl_block, "decrease_power", 2)
# #                                 if inc and inc > 0:
# #                                     power = int(inc)
# #                                 elif dec and dec > 0:
# #                                     power = max(0, rated_power - int(dec))
# #                         regs[offset] = power
# #                         print("___Inside inverter---",power)
# #                         print(regs[offset])

# #                 elif name.startswith("L") and "voltage" in name:
# #                     regs[offset] = int(230 + 5 * math.sin(2 * math.pi * hour_frac))
# #                 elif name == "acfreq":
# #                     regs[offset] = int(499 + 2 * math.sin(2 * math.pi * hour_frac))

# #             context[slave_id].setValues(3, start_addr, regs)

# #         await asyncio.sleep(5)

# # async def launch_device(device):
# #     part_num = device["part_num"]
# #     ip = device["modbus_tcp_details"]["IP"]
# #     port = int(device["modbus_tcp_details"]["port"])
# #     slave_id = int(device["modbus_tcp_details"]["slave_id"])
# #     role = device.get("role")

# #     logger.info(f"[{part_num} - {role}] Starting Modbus TCP server on {ip}:{port}")

# #     block_map = build_datablock(part_num)
# #     store = ModbusSlaveContext()
# #     for _, (db, start, _) in block_map.items():
# #         store.setValues(3, start, db.values)

# #     context = ModbusServerContext(slaves={slave_id: store}, single=False)
# #     GLOBAL_CONTEXTS[part_num] = (context, slave_id)

# #     identity = ModbusDeviceIdentification()
# #     identity.VendorName = "SimCorp"
# #     identity.ProductCode = part_num
# #     identity.ProductName = part_num
# #     identity.ModelName = "VirtualDevice"
# #     identity.MajorMinorRevision = "1.0"

# #     asyncio.create_task(update_dynamic_values(context, slave_id, part_num, role))
# #     await StartAsyncTcpServer(context, identity=identity, address=(ip, port))

# # async def main():
# #     site_id = installer_cfg.get("site id", "NO_SITE")
# #     devices = installer_cfg.get("device_list", [])
# #     logger.info(f"Installing site: {site_id}")
# #     tasks = [launch_device(dev) for dev in devices]
# #     await asyncio.gather(*tasks)

# # if __name__ == "__main__":
# #     asyncio.run(main())

# import asyncio
# import logging
# import json
# import math
# import time
# from pymodbus.server.async_io import StartAsyncTcpServer
# from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
# from pymodbus.device import ModbusDeviceIdentification

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# with open("installer_cfg.json") as f:
#     installer_cfg = json.load(f)

# with open("modbus_registers.json") as f:
#     register_defs = json.load(f)

# with open("control_register.json") as f:
#     control_defs = json.load(f)

# GLOBAL_CONTEXTS = {}  # {part_num: (context, slave_id)}

# def build_datablock(part_num):
#     if part_num not in register_defs:
#         raise ValueError(f"No register definition for part number: {part_num}")
#     data_blocks = {}
#     map_blocks = register_defs[part_num]["map"]
#     for block_key, block in map_blocks.items():
#         start = block["start_address"] - 1
#         length = block["Length"]
#         values = [0] * length
#         data_blocks[block_key] = (ModbusSequentialDataBlock(start, values), start, length)
#     return data_blocks

# def generate_bell_curve_value(hour_fraction, peak=60000):
#     mean = 0.5
#     std_dev = 0.15
#     return int(peak * math.exp(-((hour_fraction - mean) ** 2) / (2 * std_dev ** 2)))

# def get_control_value(context, slave_id, ctrl_block, name, size=1):
#     if name not in ctrl_block["data"]:
#         return None
#     meta = ctrl_block["data"][name]
#     offset = meta["offset"]
#     start_addr = ctrl_block["start_address"] - 1
#     length = ctrl_block["Length"]
#     regs = context[slave_id].getValues(3, start_addr, length)
#     if offset + size > len(regs):
#         return None
#     if size == 2:
#         return (regs[offset] << 16) + regs[offset + 1]
#     return regs[offset]

# def safe_read(part_num, block_key, offset):
#     try:
#         context, slave_id = GLOBAL_CONTEXTS[part_num]
#         block = register_defs[part_num]["map"][block_key]
#         start_addr = block["start_address"] - 1
#         length = block["Length"]
#         regs = context[slave_id].getValues(3, start_addr, length)
#         return regs[offset]
#     except Exception as e:
#         logger.warning(f"Failed to read {part_num}: {e}")
#         return 0

# async def update_dynamic_values(context, slave_id, part_num, role=None):
#     if part_num not in register_defs or "map" not in register_defs[part_num]:
#         logger.warning(f"No data map for device {part_num}")
#         return

#     reg_blocks = register_defs[part_num]["map"]
#     rated_power = 60000
#     for d in installer_cfg["device_list"]:
#         if d["part_num"] == part_num and "rated_power" in d:
#             rated_power = int(d["rated_power"])
#             break

#     ctrl_block = control_defs.get(part_num, {}).get("block1")

#     while True:
#         now = time.localtime()
#         hour = now.tm_hour + now.tm_min / 60
#         hour_frac = (now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec) / 86400

#         for block_name, block in reg_blocks.items():
#             if "data" not in block:
#                 continue

#             data_map = block["data"]
#             start_addr = block["start_address"] -1
#             length = block["Length"]
#             regs = list(context[slave_id].getValues(3, start_addr, length)) 

#             for name, meta in data_map.items():
#                 offset = meta["offset"]
#                 if name == "total_power":
#                     if role == "load_meter":
#                         if 7 <= hour < 18:
#                             power = 80000
#                             print("___Inside load---", power)
#                             if 15 <= hour < 15.5:
#                                 power = int(0.5 * power)
#                         else:
#                             power = 10000
#                         regs[offset] = power
#                         print(regs[offset])

#                     elif role == "grid_meter":
#                         inverter_power = safe_read("GROWATT123", "block1", 3)
#                         load_power = safe_read("UMG104", "block1", 3)
#                         power = max(0, load_power - inverter_power)
#                         regs[offset] = power
#                         print("___Inside Grid---", power)

#                     else:
#                         power = generate_bell_curve_value(hour_frac, rated_power)
#                         if ctrl_block:
#                             en = get_control_value(context, slave_id, ctrl_block, "power_limit_en")
#                             if en == 1:
#                                 inc = get_control_value(context, slave_id, ctrl_block, "increase_power", 2)
#                                 dec = get_control_value(context, slave_id, ctrl_block, "decrease_power", 2)
#                                 if inc and inc > 0:
#                                     power = int(inc)
#                                 elif dec and dec > 0:
#                                     power = max(0, rated_power - int(dec))
#                         regs[offset] = power
#                         print("___Inside inverter---", power)
#                         print(regs[offset])

#                 elif name.startswith("L") and "voltage" in name:
#                     regs[offset] = int(230 + 5 * math.sin(2 * math.pi * hour_frac))
#                 elif name == "acfreq":
#                     regs[offset] = int(499 + 2 * math.sin(2 * math.pi * hour_frac))

#             context[slave_id].setValues(3, start_addr, regs)

#         await asyncio.sleep(5)

# async def launch_device(device):
#     part_num = device["part_num"]
#     ip = device["modbus_tcp_details"]["IP"]
#     port = int(device["modbus_tcp_details"]["port"])
#     slave_id = int(device["modbus_tcp_details"]["slave_id"])
#     role = device.get("role")

#     logger.info(f"[{part_num} - {role}] Starting Modbus TCP server on {ip}:{port}")

#     block_map = build_datablock(part_num)
#     store = ModbusSlaveContext()
#     for _, (db, start, _) in block_map.items():
#         store.setValues(3, start, db.values)

#     context = ModbusServerContext(slaves={slave_id: store}, single=False)
#     GLOBAL_CONTEXTS[part_num] = (context, slave_id)

#     identity = ModbusDeviceIdentification()
#     identity.VendorName = "SimCorp"
#     identity.ProductCode = part_num
#     identity.ProductName = part_num
#     identity.ModelName = "VirtualDevice"
#     identity.MajorMinorRevision = "1.0"

#     asyncio.create_task(update_dynamic_values(context, slave_id, part_num, role))
#     await StartAsyncTcpServer(context, identity=identity, address=(ip, port))

# async def main():
#     site_id = installer_cfg.get("site id", "NO_SITE")
#     devices = installer_cfg.get("device_list", [])
#     logger.info(f"Installing site: {site_id}")
#     tasks = [launch_device(dev) for dev in devices]
#     await asyncio.gather(*tasks)

# if __name__ == "__main__":
#     asyncio.run(main())
###########LASTT_WORKING_CODE######################################################

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

with open("installer_cfg.json") as f:
    installer_cfg = json.load(f)

with open("modbus_registers.json") as f:
    register_defs = json.load(f)

with open("control_register.json") as f:
    control_defs = json.load(f)

GLOBAL_CONTEXTS = {}
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
    if name not in ctrl_block["data"]:
        return None
    meta = ctrl_block["data"][name]
    offset = meta["offset"]
    start_addr = ctrl_block["start_address"] - 1
    length = ctrl_block["Length"]
    regs = context[slave_id].getValues(3, start_addr, length)
    if offset + size > len(regs):
        return None
    if size == 2:
        return (regs[offset] << 16) + regs[offset + 1]
    return regs[offset]

async def update_dynamic_values(context, slave_id, part_num, role=None):
    if part_num not in register_defs or "map" not in register_defs[part_num]:
        logger.warning(f"No data map for device {part_num}")
        return

    reg_blocks = register_defs[part_num]["map"]
    rated_power = 60000
    for d in installer_cfg["device_list"]:
        if d["part_num"] == part_num and "rated_power" in d:
            rated_power = int(d["rated_power"])
            break

    ctrl_block = control_defs.get(part_num, {}).get("block1")

    while True:
        now = time.localtime()
        hour = now.tm_hour + now.tm_min / 60
        hour_frac = (now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec) / 86400

        for block_name, block in reg_blocks.items():
            if "data" not in block:
                continue

            data_map = block["data"]
            start_addr = block["start_address"] - 1
            length = block["Length"]
            regs = list(context[slave_id].getValues(3, start_addr, length))

            for name, meta in data_map.items():
                offset = meta["offset"]
                if name == "total_power":
                    if role == "load_meter":
                        load_val = 60000 if 7 <= hour < 18 else 0
                        if 15 <= hour < 15.5:
                            load_val = int(0.5 * load_val)
                        regs[offset] = load_val
                        GLOBAL_POWER_STATE["load_power"] = load_val
                        print(offset)
                        print("_________LOAD_________________")
                    elif role == "grid_meter":
                        inv = GLOBAL_POWER_STATE.get("inverter_power", 0)
                        load = GLOBAL_POWER_STATE.get("load_power", 0)
                        grid_val = max(0, load - inv)
                        regs[offset] = grid_val
                        print(offset)
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
                        print(offset)

                elif name.startswith("L") and "voltage" in name:
                    regs[offset] = int(230 + 5 * math.sin(2 * math.pi * hour_frac))
                elif name == "acfreq":
                    regs[offset] = int(499 + 2 * math.sin(2 * math.pi * hour_frac))

            context[slave_id].setValues(3, start_addr, regs)

        await asyncio.sleep(5)

async def launch_device(device):
    part_num = device["part_num"]
    ip = device["modbus_tcp_details"]["IP"]
    port = int(device["modbus_tcp_details"]["port"])
    slave_id = int(device["modbus_tcp_details"]["slave_id"])
    role = device.get("role")

    logger.info(f"[{part_num} - {role}] Starting Modbus TCP server on {ip}:{port}")

    block_map = build_datablock(part_num)
    store = ModbusSlaveContext()
    for _, (db, start, _) in block_map.items():
        store.setValues(3, start, db.values)

    context = ModbusServerContext(slaves={slave_id: store}, single=False)
    GLOBAL_CONTEXTS[part_num] = (context, slave_id)

    identity = ModbusDeviceIdentification()
    identity.VendorName = "SimCorp"
    identity.ProductCode = part_num
    identity.ProductName = part_num
    identity.ModelName = "VirtualDevice"
    identity.MajorMinorRevision = "1.0"

    asyncio.create_task(update_dynamic_values(context, slave_id, part_num, role))
    print(context)
    await StartAsyncTcpServer(context, identity=identity, address=(ip, port))

async def main():
    site_id = installer_cfg.get("site id", "NO_SITE")
    devices = installer_cfg.get("device_list", [])
    logger.info(f"Installing site: {site_id}")
    tasks = [launch_device(dev) for dev in devices]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
