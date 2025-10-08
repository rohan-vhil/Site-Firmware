# launcher.py
import os
import sys
import json
import threading
import time
from pymodbus.client import ModbusSerialClient

# Import your project's custom modules
from edge_device import main_thread
from edge_device.reports_handling import report_handler as rpthndler
from edge_device.control import control_base as ctrl
import path_config

def setup_platform_config():
    """
    Sets up the platform-specific base path for the entire project.
    This should point to your project's absolute root directory.
    """
    # The '~' symbol will be automatically expanded to the user's home directory
    # (e.g., /home/edge_device)
    return os.path.expanduser("~/edge_device/")

def create_rtu_clients(config_path: str) -> dict:
    """
    Reads the installer config and creates clients ONLY for Modbus RTU (serial) devices.
    TCP devices handle their own client creation since they don't need special hardware access.
    """
    rtu_clients = {}

    # This path is correct, relative to the project root
    installer_cfg_path = os.path.join(config_path, "submodules", "RpiBackend", "app", "json_files", "installer_cfg.json")

    try:
        with open(installer_cfg_path) as f:
            installer_cfg = json.load(f)
        print("✅ Successfully loaded installer_cfg.json from submodules.")
    except FileNotFoundError:
        print(f"❌ ERROR: Could not find installer config at {installer_cfg_path}")
        return {}

    for device in installer_cfg.get("device_list", []):
        # We only need to pre-create clients for RTU devices
        if device.get('comm_type') == 'modbus-rtu':
            details = device['modbus_rtu_details']
            port = details['port']
            
            if port not in rtu_clients:
                print(f"Initializing Modbus RTU client for port: {port} ...")
                try:
                    client = ModbusSerialClient(
                        method="rtu",
                        port=port,
                        baudrate=int(details['baudrate']),
                        timeout=1,
                        parity=details['parity'][0].upper(),
                        stopbits=int(details['stop_bits'])
                    )
                    rtu_clients[port] = client
                except Exception as e:
                    print(f"Failed to create client for port {port}: {e}")
    return rtu_clients

if __name__ == "__main__":
    print("🚀 Starting Firmware...")

    # 1. Set up the absolute base path for the project
    BASE_PATH = setup_platform_config()
    print(f"Using project root (BASE_PATH): {BASE_PATH}")
    
    # 2. Assign the base path to the global config object so other modules can use it
    path_config.path_cfg.base_path = BASE_PATH

    # 3. Pre-create all hardware-specific Modbus RTU clients
    all_rtu_clients = create_rtu_clients(BASE_PATH)
    
    # 4. Initialize the application's device list.
    #    This function will handle BOTH TCP and RTU devices.
    #    It will use the pre-created clients for RTU devices.
    main_thread.readDeviceList(BASE_PATH, all_rtu_clients)

    # 5. Start the main application threads if the config file was loaded successfully
    if main_thread.install_file:
        print("Starting data acquisition and reporting threads...")
        rpthndler.data_handler = rpthndler.dataBank()
        
        t1 = threading.Thread(target=main_thread.getData)
        t2 = threading.Thread(target=rpthndler.data_handler.runDataLoop)

        t1.start()
        t2.start()

        t1.join()
        t2.join()
        print("Threads finished.")
    else:
        print("Device installation file not found or failed to read. Application will not start.")
