import os
import threading
import time
from modbus_master import modbusmasterapi as mbus
import json
import control.control_base as ctrl
import reports_handling.report_handler as rpthndler
import path_config
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from getmac import get_mac_address as gma
import sys
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("thread_monitor.log"),
        logging.StreamHandler()
    ]
)

sys.path.insert(0,'../submodules')

install_file : bool = False
send_project_details : bool = False
logger_enrolled : bool = False

def getAddrMapFromPartNum(part,addr_map : dict,ctrl_map:dict={}):
    with open(path_config.path_cfg.base_path + 'modbus_mappings/mappings.json') as mapfile:
        mbus_maps = json.load(mapfile)
        addr_map['map'] = mbus_maps[part]

    with open(path_config.path_cfg.base_path + 'modbus_mappings/control_registers.json') as ctrlfile:
        mbus_maps = json.load(ctrlfile)
        ctrl_map['map'] = mbus_maps[part]

def readDeviceList():
    print(path_config.path_cfg.base_path)
    global install_file
    global send_project_details
    install_file_path = path_config.path_cfg.base_path + "../submodules/RpiBackend/app/json_files/installer_cfg.json"
    os.system("cat " + path_config.path_cfg.base_path + "../submodules/RpiBackend/app/json_files/installer_cfg.json")
    project_device_path = path_config.path_cfg.base_path + "../submodules/RpiBackend/app/json_files/project_devices.json"
    
    if(not os.path.exists(project_device_path)):
        send_project_details = True
        install_file = False
        return
    else:
        print("install file present")
        install_file = True

    with open(install_file_path) as installer_file:
        installer_cfg = json.load(installer_file)

    ctrl.site_id = installer_cfg["site id"]
    ctrl.controller_id = str(gma())

    global number_of_devices
    number_of_devices = len(installer_cfg["device_list"])
    print('Number of devices is',number_of_devices)
    i=-1
    for device in installer_cfg["device_list"]:
        i+=1
        for x in device:
            print(x)
            
        device_id = device["device_id"]
        print(device['phases'])  
        num_phases = eval(device['num_phases'])
        phase = [int(s) for s in device["phases"].split(',')]

        if(device['comm_type']== 'modbus-tcp'):
            devicetype = ctrl.deviceType_l2e[device['device_type']]
            tcp_details = device['modbus_tcp_details']
            ip = tcp_details['IP']
            read_map = {}   
            ctrl_map={}
            getAddrMapFromPartNum(device["part_num"],read_map,ctrl_map)
            slave_id = eval(tcp_details.get('slave_id', '1'))
            ctrl.device_list.append(mbus.modbusTCPDevice(devicetype, ctrl.commType.modbus_tcp,ip,port=eval(tcp_details['port']),slave_id=slave_id,address_map=read_map,ctrl_map=ctrl_map,cfg=device))

        elif(device['comm_type'] == 'modbus-rtu'):
            devicetype = ctrl.deviceType_l2e[device['device_type']]
            rtu_details = device['modbus_rtu_details']
            port = rtu_details['port']
            slave_id=eval(rtu_details['slave_id'])
            parity=(rtu_details['parity'])
            baud = eval(rtu_details['baudrate'])
            stop_bits=eval(rtu_details['stop_bits'])
            read_map = {}
            ctrl_map = {}
            getAddrMapFromPartNum(device["part_num"],read_map,ctrl_map)
            ctrl.device_list.append(mbus.modbusRTUDevice(devicetype,ctrl.commType.modbus_rtu,read_map,ctrl_map,port,parity,stop_bits,baud,slave_id,cfg=device))

        elif(device['comm_type'] == 'none'):
            ctrl.device_list.append(ctrl.systemDevice(devicetype=ctrl.deviceType.DG,commtype=ctrl.commType.none))

        ctrl.device_list[-1].device_id = device_id
        ctrl.device_list[-1].num_phases = num_phases
        ctrl.device_list[-1].createMeasureRegisterMap()
        ctrl.device_list[-1].createControlRegisterMap()
        ctrl.device_list[-1].phase = phase
        if("rated_power") in device:
            ctrl.device_list[-1].rated_power = eval(device["rated_power"])
            print("rated_power is : ")
            print(ctrl.device_list[-1].rated_power)
        if("connected_to" in device):
            ctrl.device_list[-1].connected_to = ctrl.deviceType_l2e[device["connected_to"]]
            print("connected_to device type is : ")
            print(device["connected_to"])
        
    print("maps are : ")

    site_response = requests.Response()
    for device in ctrl.device_list:
        print(device.addr_map,device.device_id,device.device_type)

    with open(path_config.path_cfg.base_path + "status_cfg.json") as status_file:
        status_cfg = json.load(status_file)
        print("site create : ",status_cfg["site_created"])
        if(not eval(status_cfg["site_created"])):
            with open(site_device_path) as site_device_file:
                site_device_cfg = json.load(site_device_file)
                try:
                    site_response = requests.post("https://app.enercog.com//ui/customer/project/create-project-device",json=site_device_cfg,verify=False)
                    print(site_response.status_code,site_response.content)
                except Exception as e:
                    print(site_response)
                    print(e)
        if(site_response.status_code == 200 or site_response.status_code == 201):
            status_cfg["site_created"] = "1"
            with open("status_cfg.json","w") as status_file:
                json.dump(status_cfg,status_file)

def getData():
    global install_file
    while not os.path.exists(path_config.path_cfg.base_path + "devices.json"):
        install_file = False
        pass
    install_file = True

    while install_file:
        with open(path_config.path_cfg.base_path + "reports_handling/report_cfg.json") as report_file:
            report_cfg = json.load(report_file)

        read_period = report_cfg["reading_period"] 
        for device in ctrl.device_list:
            try:
                if(device.comm_type == ctrl.commType.modbus_tcp or device.comm_type == ctrl.commType.modbus_rtu):
                    device.decodeData(mbus.getModbusData(device))
            except Exception as e:
                print(e)

        rpthndler.data_handler.aggData(ctrl.getAllData())
        #ctrl.runSysControlLoop()
        #print("control Executed successfully")
        #logging.info("control executed successfully")
        time.sleep(read_period)

def getDataThread():
    logging.info("getData thread started.")
    try:
        getData()
    except Exception as e:
        logging.error(f"getData thread crashed: {e}", exc_info=True)

def runDataLoopThread():
    logging.info("runDataLoop thread started.")
    try:
        rpthndler.data_handler.runDataLoop()
    except Exception as e:
        logging.error(f"runDataLoop thread crashed: {e}", exc_info=True)

def triggerThreads():
    global install_file
    install_file = False

if __name__ == "__main__":
    print("run file")
    logging.info("Program started")
    path_config.path_cfg = path_config.pathConfig()

    while not install_file:
        readDeviceList()
        pass

    rpthndler.data_handler = rpthndler.dataBank()

    t1 = threading.Thread(target=getDataThread, name="getDataThread")
    t2 = threading.Thread(target=runDataLoopThread, name="runDataLoopThread")

    t1.start()
    t2.start()

    # Thread monitor loop
    while True:
        if not t1.is_alive():
            logging.error("getDataThread has stopped unexpectedly.")
            print("getDataThread has crashed.")
            break
        else:
            logging.info("getDataThread is running.")

        if not t2.is_alive():
            logging.error("runDataLoopThread has stopped unexpectedly.")
            print("runDataLoopThread has crashed.")
            break
        else:
            logging.info("runDataLoopThread is running.")

        time.sleep(10)  # Check every 10 seconds

    t1.join()
    t2.join()
    print("thread monitor exiting")
