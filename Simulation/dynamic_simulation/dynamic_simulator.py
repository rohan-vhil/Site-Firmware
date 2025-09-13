# import asyncio
# import logging
# import json
# import math
# import time
# from pymodbus.server.async_io import StartAsyncTcpServer
# from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
# from pymodbus.device import ModbusDeviceIdentification

# # --- Basic Configuration ---
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # --- Loading Configuration Files ---
# try:
#     with open("installer_cfg.json") as f:
#         installer_cfg = json.load(f)
#     with open("modbus_registers.json") as f:
#         register_defs = json.load(f)
#     with open("control_register.json") as f:
#         control_defs = json.load(f)
# except FileNotFoundError as e:
#     logger.error(f"Configuration file not found: {e}. Please ensure all JSON files are in the same directory.")
#     exit()

# # --- Global State Management ---
# # This dictionary will hold the current power of all devices, keyed by their role and slave_id
# GLOBAL_POWER_STATE = {
#     "inverters": {},
#     "loads": {}
# }

# def build_datablock(part_num):
#     """Constructs a Modbus data block from register definitions."""
#     if part_num not in register_defs:
#         logger.warning(f"No register definition for part number: {part_num}. Using a default empty block.")
#         return { "default": (ModbusSequentialDataBlock(0, [0]*10), 0, 10) }

#     data_blocks = {}
#     map_blocks = register_defs[part_num].get("map", {})
#     for block_key, block in map_blocks.items():
#         start = block["start_address"] - 1 
#         length = block["Length"]
#         values = [0] * length
#         data_blocks[block_key] = (ModbusSequentialDataBlock(start, values), start, length)
#     return data_blocks

# def generate_bell_curve_value(hour_fraction, peak=60000):
#     """Generates a power value following a bell curve based on the time of day."""
#     mean = 0.5
#     std_dev = 0.15
#     return int(peak * math.exp(-((hour_fraction - mean) ** 2) / (2 * std_dev ** 2)))

# def get_control_value(context, slave_id, ctrl_block, name, size=1):
#     """Reads a control value from the datastore."""
#     if not ctrl_block or name not in ctrl_block.get("data", {}):
#         return None
    
#     meta = ctrl_block["data"][name]
#     offset = meta["offset"]
#     start_addr = ctrl_block["start_address"] - 1
#     length = ctrl_block["Length"]
    
#     try:
#         regs = context[slave_id].getValues(3, start_addr, length)
#         if not regs or offset + size > len(regs):
#             return None
#         val = regs[offset]
#         if size == 2:
#             val = (regs[offset] << 16) + regs[offset + 1]
#         if val != 0:
#             logger.info(f"Control value '{name}' for slave {slave_id} read from firmware: {val}")
#         return val
#     except Exception as e:
#         logger.error(f"Error in get_control_value for '{name}': {e}")
#         return None

# async def update_dynamic_values(context, slave_id, part_num, role):
#     """
#     This function runs in a continuous loop to update the register values
#     for a single simulated device, based on its defined role and configuration.
#     """
#     if part_num not in register_defs:
#         return # Do not run updater for undefined devices

#     reg_blocks = register_defs[part_num]["map"]
#     device_config = next((d for d in installer_cfg["device_list"] if d["modbus_tcp_details"]["slave_id"] == slave_id), {})
#     rated_power = int(device_config.get("rated_power", 0))
#     ctrl_block = control_defs.get(part_num, {}).get("block1")

#     while True:
#         now = time.localtime()
#         hour = now.tm_hour + now.tm_min / 60.0
#         hour_frac = (now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec) / 86400.0
        
#         power_val = 0
        
#         # --- DYNAMIC LOGIC BASED ON ROLE ---
#         if role == "inverter":
#             power_val = generate_bell_curve_value(hour_frac, rated_power)
#             if ctrl_block:
#                 en = get_control_value(context, slave_id, ctrl_block, "power_limit_en")
#                 if en == 1:
#                     # Check for value control
#                     if "power_limit_value" in ctrl_block["data"]:
#                         limit_val = get_control_value(context, slave_id, ctrl_block, "power_limit_value", 2)
#                         if limit_val is not None: power_val = limit_val
#                     # Check for percentage control
#                     elif "power_limit_pct" in ctrl_block["data"]:
#                         limit_pct = get_control_value(context, slave_id, ctrl_block, "power_limit_pct")
#                         if limit_pct is not None:
#                             power_val = int(rated_power * (limit_pct / 1000.0))
#             GLOBAL_POWER_STATE["inverters"][slave_id] = power_val

#         elif role == "load_meter":
#             power_val = 80000 if 7 <= hour < 18 else 0
#             if 15 <= hour < 15.5: power_val = 30000
#             GLOBAL_POWER_STATE["loads"][slave_id] = power_val

#         elif role == "grid_meter":
#             total_inverter_power = sum(GLOBAL_POWER_STATE["inverters"].values())
#             print(total_inverter_power)
#             total_load_power = sum(GLOBAL_POWER_STATE["loads"].values())
#             power_val = max(0, total_load_power - total_inverter_power)

#         # --- Populate Registers ---
#         for block_name, block in reg_blocks.items():
#             start_addr = block["start_address"] - 1
#             data_map = block["data"]
#             regs = [0] * block["Length"]
            
#             voltage_val = int(230 + 5 * math.sin(2 * math.pi * hour_frac))
#             freq_val = int(499 + 2 * math.sin(2 * math.pi * hour_frac))

#             for name, meta in data_map.items():
#                 offset = meta["offset"]
#                 if offset >= len(regs): continue

#                 if name == "total_power":
#                     if meta.get("format") == "decode_32bit_uint":
#                         high = power_val >> 16
#                         low = power_val & 0xFFFF
#                         if offset + 1 < len(regs):
#                             regs[offset], regs[offset+1] = high, low
#                 elif name.startswith("L") and "voltage" in name:
#                     regs[offset] = voltage_val
#                 elif name == "acfreq":
#                     regs[offset] = freq_val
            
#             context[slave_id].setValues(3, start_addr, regs)

#         await asyncio.sleep(5)


# async def main():
#     """Main function to launch the single, multi-device simulator."""
#     logger.info(f"Initializing site: {installer_cfg.get('site id', 'NO_SITE')}")

#     slaves = {}
#     for dev in installer_cfg.get("device_list", []):
#         part_num = dev["part_num"]
#         slave_id = int(dev["modbus_tcp_details"]["slave_id"])
#         role = dev.get("role", "device")
        
#         # Initialize power state entries
#         if role == 'inverter': GLOBAL_POWER_STATE['inverters'][slave_id] = 0
#         if role == 'load_meter': GLOBAL_POWER_STATE['loads'][slave_id] = 0

#         logger.info(f"[{part_num} - {role}] Initializing slave device with ID {slave_id}")
        
#         block_map = build_datablock(part_num)
#         store = ModbusSlaveContext()
#         for _, (db, start, _) in block_map.items():
#             store.setValues(3, start, db.values)
#         slaves[slave_id] = store

#     server_context = ModbusServerContext(slaves=slaves, single=False)

#     # Start one update task for each configured device
#     for dev in installer_cfg.get("device_list", []):
#         asyncio.create_task(
#             update_dynamic_values(
#                 context=server_context,
#                 slave_id=int(dev["modbus_tcp_details"]["slave_id"]),
#                 part_num=dev["part_num"],
#                 role=dev.get("role")
#             )
#         )

#     server_ip = "127.0.0.1"
#     server_port = 8507 
#     logger.info(f"Starting single Modbus TCP server on {server_ip}:{server_port} for all devices.")

#     identity = ModbusDeviceIdentification()
#     identity.VendorName = "SimCorp"
#     identity.ProductCode = "Dynamic Multi-Device Simulator"
#     identity.ProductName = "Dynamic Simulator"
#     identity.ModelName = "VirtualGateway"
#     identity.MajorMinorRevision = "3.1"

#     await StartAsyncTcpServer(context=server_context, identity=identity, address=(server_ip, server_port))

# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         logger.info("Simulation stopped by user.")


import asyncio
import logging
import json
import math
import time
from pymodbus.server.async_io import StartAsyncTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Loading Configuration Files ---
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

# --- Global State Management ---
# This dictionary will hold the current power of all devices, keyed by their role and slave_id
GLOBAL_POWER_STATE = {
    "inverters": {},
    "loads": {}
}

def build_datablock(part_num):
    """Constructs a Modbus data block from register definitions."""
    if part_num not in register_defs:
        logger.warning(f"No register definition for part number: {part_num}. Using a default empty block.")
        return { "default": (ModbusSequentialDataBlock(0, [0]*10), 0, 10) }

    data_blocks = {}
    map_blocks = register_defs[part_num].get("map", {})
    for block_key, block in map_blocks.items():
        start = block["start_address"] - 1 
        length = block["Length"]
        values = [0] * length
        data_blocks[block_key] = (ModbusSequentialDataBlock(start, values), start, length)
    return data_blocks

def generate_bell_curve_value(hour_fraction, peak=60000):
    """Generates a power value following a bell curve based on the time of day."""
    mean = 0.5
    std_dev = 0.15
    return int(peak * math.exp(-((hour_fraction - mean) ** 2) / (2 * std_dev ** 2)))

def get_control_value(context, slave_id, ctrl_block, name, size=1):
    """Reads a control value from the datastore."""
    if not ctrl_block or name not in ctrl_block.get("data", {}):
        return None
    
    meta = ctrl_block["data"][name]
    offset = meta["offset"]
    start_addr = ctrl_block["start_address"] - 1
    length = ctrl_block["Length"]
    
    try:
        regs = context[slave_id].getValues(3, start_addr, length)
        if not regs or offset + size > len(regs):
            return None
        val = regs[offset]
        if size == 2:
            val = (regs[offset] << 16) + regs[offset + 1]
        if val != 0:
            logger.info(f"Control value '{name}' for slave {slave_id} read from firmware: {val}")
        return val
    except Exception as e:
        logger.error(f"Error in get_control_value for '{name}': {e}")
        return None

async def update_dynamic_values(context, slave_id, part_num, role):
    """
    This function runs in a continuous loop to update the register values
    for a single simulated device, based on its defined role and configuration.
    """
    if part_num not in register_defs:
        return # Do not run updater for undefined devices

    reg_blocks = register_defs[part_num]["map"]
    device_config = next((d for d in installer_cfg["device_list"] if d["modbus_tcp_details"]["slave_id"] == slave_id), {})
    rated_power = int(device_config.get("rated_power", 0))
    ctrl_block = control_defs.get(part_num, {}).get("block1")

    while True:
        now = time.localtime()
        hour = now.tm_hour + now.tm_min / 60.0
        hour_frac = (now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec) / 86400.0
        
        power_val = 0
        
        # --- DYNAMIC LOGIC BASED ON ROLE ---
        if role == "inverter":
            # Default power generation is based on the time-of-day bell curve
            power_val = generate_bell_curve_value(hour_frac, rated_power)
            
            if ctrl_block:
                en = get_control_value(context, slave_id, ctrl_block, "power_limit_en")
                if en == 1:
                    # Firmware has enabled power limit control
                    
                    # Check for value control
                    if "power_limit_value" in ctrl_block["data"]:
                        limit_val = get_control_value(context, slave_id, ctrl_block, "power_limit_value", 2)
                        if limit_val is not None:
                            # If the limit is set to max rated power, it means "follow environment".
                            # Otherwise, use the fixed value.
                            if limit_val != rated_power:
                                power_val = limit_val
                    
                    # Check for percentage control
                    elif "power_limit_pct" in ctrl_block["data"]:
                        limit_pct = get_control_value(context, slave_id, ctrl_block, "power_limit_pct")
                        if limit_pct is not None:
                             # If the limit is 100% (1000), it means "follow environment".
                             # Otherwise, calculate the fixed power from the percentage.
                            if limit_pct != 1000:
                                power_val = int(rated_power * (limit_pct / 1000.0))

            GLOBAL_POWER_STATE["inverters"][slave_id] = power_val

        elif role == "load_meter":
            power_val = 80000 if 7 <= hour < 18 else 0
            
            if 15 <= hour < 15.5: power_val = 30000
            GLOBAL_POWER_STATE["loads"][slave_id] = power_val

        elif role == "grid_meter":
            total_inverter_power = sum(GLOBAL_POWER_STATE["inverters"].values())
            total_load_power = sum(GLOBAL_POWER_STATE["loads"].values())
            power_val = max(0, total_load_power - total_inverter_power)

        # --- Populate Registers ---
        for block_name, block in reg_blocks.items():
            start_addr = block["start_address"] - 1
            data_map = block["data"]
            regs = [0] * block["Length"]
            
            voltage_val = int(230 + 5 * math.sin(2 * math.pi * hour_frac))
            freq_val = int(499 + 2 * math.sin(2 * math.pi * hour_frac))

            for name, meta in data_map.items():
                offset = meta["offset"]
                if offset >= len(regs): continue

                if name == "total_power":
                    if meta.get("format") == "decode_32bit_uint":
                        high = power_val >> 16
                        low = power_val & 0xFFFF
                        if offset + 1 < len(regs):
                            regs[offset], regs[offset+1] = high, low
                elif name.startswith("L") and "voltage" in name:
                    regs[offset] = voltage_val
                elif name == "acfreq":
                    regs[offset] = freq_val
            
            context[slave_id].setValues(3, start_addr, regs)

        await asyncio.sleep(5)


async def main():
    """Main function to launch the single, multi-device simulator."""
    logger.info(f"Initializing site: {installer_cfg.get('site id', 'NO_SITE')}")

    slaves = {}
    for dev in installer_cfg.get("device_list", []):
        part_num = dev["part_num"]
        slave_id = int(dev["modbus_tcp_details"]["slave_id"])
        role = dev.get("role", "device")
        
        # Initialize power state entries
        if role == 'inverter': GLOBAL_POWER_STATE['inverters'][slave_id] = 0
        if role == 'load_meter': GLOBAL_POWER_STATE['loads'][slave_id] = 0

        logger.info(f"[{part_num} - {role}] Initializing slave device with ID {slave_id}")
        
        block_map = build_datablock(part_num)
        store = ModbusSlaveContext()
        for _, (db, start, _) in block_map.items():
            store.setValues(3, start, db.values)
        slaves[slave_id] = store

    server_context = ModbusServerContext(slaves=slaves, single=False)

    # Start one update task for each configured device
    for dev in installer_cfg.get("device_list", []):
        asyncio.create_task(
            update_dynamic_values(
                context=server_context,
                slave_id=int(dev["modbus_tcp_details"]["slave_id"]),
                part_num=dev["part_num"],
                role=dev.get("role")
            )
        )

    server_ip = "127.0.0.1"
    server_port = 8507 
    logger.info(f"Starting single Modbus TCP server on {server_ip}:{server_port} for all devices.")

    identity = ModbusDeviceIdentification()
    identity.VendorName = "SimCorp"
    identity.ProductCode = "Dynamic Multi-Device Simulator"
    identity.ProductName = "Dynamic Simulator"
    identity.ModelName = "VirtualGateway"
    identity.MajorMinorRevision = "3.1"

    await StartAsyncTcpServer(context=server_context, identity=identity, address=(server_ip, server_port))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Simulation stopped by user.")
