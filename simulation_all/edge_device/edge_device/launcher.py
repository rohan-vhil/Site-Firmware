# launcher.py

import os
import sys
import json
import threading
import time
from pymodbus.client import ModbusSerialClient

# Import your existing, now-decoupled, modules
import main_thread
import reports_handling.report_handler as rpthndler
from control import control_base as ctrl
import path_config # <--- ADD THIS LINE TO FIX THE ERROR

def setup_platform_config():
    """
    Sets up platform-specific configurations.
    *** EDIT THIS FUNCTION WHEN MOVING TO A NEW CONTROLLER ***
    """
    if sys.platform.startswith('linux'):
        # Configuration for a Raspberry Pi or other Linux system
        return "/home/edge_device/edge_device/"
    elif sys.platform == 'win32':
        # Configuration for a Windows PC
        return "C:/firmware/config/"
    else:
        # Default configuration for an unknown system
        return "./" # Assumes config files are in the same directory

def create_rtu_clients(config_path: str) -> dict:
    """
    Reads the installer config and creates all necessary Modbus RTU clients.
    """
    rtu_clients = {}
    installer_cfg_path = os.path.join(config_path,"/home/edge_device/edge_device/submodules/RpiBackend/app/json_files/installer_cfg.json")

    try:
        with open(installer_cfg_path) as f:
            installer_cfg = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Could not find installer config at {installer_cfg_path}")
        return {}

    for device in installer_cfg.get("device_list", []):
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
                        parity=details['parity'][0].upper(), # 'N', 'E', 'O'
                        stopbits=int(details['stop_bits'])
                    )
                    rtu_clients[port] = client
                except Exception as e:
                    print(f"Failed to create client for port {port}: {e}")
    return rtu_clients

if __name__ == "__main__":
    print("🚀 Starting Firmware...")

    # 1. Set up platform-specific base path
    BASE_PATH = setup_platform_config()
    print(f"Using base path: {BASE_PATH}")
    
    # This makes the path available to your other modules if they need it
    # (Though passing it as an argument is a cleaner pattern)
    path_config.path_cfg.base_path = BASE_PATH

    # 2. Pre-create all hardware-specific RTU clients
    all_rtu_clients = create_rtu_clients(BASE_PATH)
    if not all_rtu_clients:
        print("No RTU devices configured or config file not found. Exiting.")
        sys.exit(1)

    # 3. Initialize the application by passing in the configurations
    main_thread.readDeviceList(BASE_PATH, all_rtu_clients)

    # 4. Start the application threads (this logic is moved from main_thread.py)
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
