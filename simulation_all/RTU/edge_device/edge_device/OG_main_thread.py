import os
import threading
import time
from modbus_master import modbusmasterapi as mbus
import json
import control.control_base as ctrl
import reports_handling.report_handler as rpthndler
import path_config
import requests
import sys
from getmac import get_mac_address as gma

# MODIFIED: Import the secure TLS server module to be run as a thread
from IEC_RTU import tls_server



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
    path_config.path_cfg = path_config.pathConfig()

    while not install_file:
        readDeviceList()
        time.sleep(2)

    rpthndler.data_handler = rpthndler.dataBank()

    # --- MODIFIED: Perform a single, initial data read BEFORE starting the server ---
    print("--- Performing initial data read to discover points... ---")
    for device in ctrl.device_list:
        if device.comm_type in [ctrl.commType.modbus_tcp, ctrl.commType.modbus_rtu]:
            device.decodeData(mbus.getModbusData(device))
    rpthndler.data_handler.aggData(ctrl.getAllData())
    initial_data = rpthndler.data_handler.avg_data.copy()
    print("--- Initial data structure captured successfully. ---")

    # --- MODIFIED: Initialize the server with the data structure, but DO NOT start it yet ---
    tls_server.initializeIECServer(initial_data)

    # --- MODIFIED: Create and start all threads, including the pre-configured server thread ---
    t_data_acquisition = threading.Thread(target=continuous_data_acquisition, daemon=True)
    t_report_handling = threading.Thread(target=rpthndler.data_handler.runDataLoop, daemon=True)
    t_iec_server = threading.Thread(target=tls_server.runServer, args=[rpthndler.data_handler], daemon=True)

    print("--- Starting all service threads (Data Acquisition, Reporting, IEC Server)... ---")
    t_data_acquisition.start()
    t_report_handling.start()
    t_iec_server.start()

    # Keep the main thread alive to allow background threads to run
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n--- Shutting down firmware... ---")
