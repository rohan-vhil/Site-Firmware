# main_thread.py

import os
import threading
import time
import json
import sys
from getmac import get_mac_address as gma

# Your project-specific imports
from modbus_master import modbusmasterapi as mbus
import control.control_base as ctrl
import reports_handling.report_handler as rpthndler
import path_config

# Import the encrypted server module we created
# Using an alias 'iec_server' for clarity
from IEC_RTU import simple_server_encrypted as iec_server

install_file: bool = False

def getAddrMapFromPartNum(part, addr_map: dict, ctrl_map: dict = {}):
    """Loads register maps for a given device part number."""
    with open(path_config.path_cfg.base_path + 'modbus_mappings/mappings.json') as mapfile:
        addr_map['map'] = json.load(mapfile)[part]
    with open(path_config.path_cfg.base_path + 'modbus_mappings/control_registers.json') as ctrlfile:
        ctrl_map['map'] = json.load(ctrlfile)[part]

def readDeviceList():
    """Reads the installer configuration and initializes all devices."""
    global install_file
    # This path might need to be adjusted based on your final project structure
    install_file_path = path_config.path_cfg.base_path + "../submodules/RpiBackend/app/json_files/installer_cfg.json"
    if not os.path.exists(install_file_path):
        print("Waiting for configuration file...")
        return
    
    install_file = True
    with open(install_file_path) as installer_file:
        installer_cfg = json.load(installer_file)
        
    ctrl.site_id = installer_cfg["site id"]
    ctrl.controller_id = str(gma())

    print(f"Number of devices is {len(installer_cfg['device_list'])}")
    for device_config in installer_cfg["device_list"]:
        devicetype = ctrl.deviceType_l2e[device_config['device_type']]
        read_map, ctrl_map = {}, {}
        getAddrMapFromPartNum(device_config["part_num"], read_map, ctrl_map)
        
        new_device = None
        if device_config['comm_type'] == 'modbus-tcp':
            tcp = device_config['modbus_tcp_details']
            new_device = mbus.modbusTCPDevice(devicetype, ctrl.commType.modbus_tcp, tcp['IP'], int(tcp['port']), int(tcp.get('slave_id', 1)), read_map, ctrl_map, device_config)
        
        if new_device:
            new_device.device_id = device_config["device_id"]
            new_device.createMeasureRegisterMap()
            new_device.createControlRegisterMap()
            ctrl.device_list.append(new_device)
    print("Device configuration loaded successfully.")

def continuous_data_acquisition():
    """Continuously reads data from all configured devices in a loop."""
    while True:
        try:
            with open(path_config.path_cfg.base_path + "reports_handling/report_cfg.json") as report_file:
                read_period = json.load(report_file)["reading_period"]

            for device in ctrl.device_list:
                try:
                    if device.comm_type in [ctrl.commType.modbus_tcp, ctrl.commType.modbus_rtu]:
                        device.decodeData(mbus.getModbusData(device))
                except Exception as e:
                    print(f"Error reading from device {device.device_id}: {e}")
            
            rpthndler.data_handler.aggData(ctrl.getAllData())
            time.sleep(read_period)
        except Exception as e:
            print(f"Main data acquisition loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("--- Starting Firmware Main Thread ---")
    
    # This assumes path_config is correctly set up to find your project files
    path_config.path_cfg = path_config.pathConfig()

    while not install_file:
        readDeviceList()
        time.sleep(2)

    rpthndler.data_handler = rpthndler.dataBank()

    # --- Start the IEC-104 encrypted server ---
    # This function loads the keys, starts the IEC-104 server, 
    # and launches the background thread for publishing encrypted data.
    iec_server.startIECServer()

    # --- Create and start all service threads ---
    # This thread continuously gets new data from your hardware
    t_data_acquisition = threading.Thread(target=continuous_data_acquisition, daemon=True)
    
    # This thread handles data aggregation and reporting
    t_report_handling = threading.Thread(target=rpthndler.data_handler.runDataLoop, daemon=True)
    
    # This thread feeds the latest data to the IEC server module
    t_iec_server = threading.Thread(target=iec_server.runServer, args=[rpthndler.data_handler], daemon=True)

    print("--- Starting all service threads (Data Acquisition, Reporting, IEC Server Data Feed)... ---")
    t_data_acquisition.start()
    t_report_handling.start()
    t_iec_server.start()

    print("--- Firmware is running. Press Ctrl+C to shut down. ---")
    # Keep the main thread alive to allow background threads to run
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n--- Shutting down firmware... ---")
