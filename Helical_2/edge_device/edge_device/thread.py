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
#from io_master import iomasterapi as io
from mqtt_master import subscribe

install_file : bool = False
send_project_details : bool = False
logger_enrolled : bool = False
import sys
sys.path.insert(0,'../submodules')
#from submodules.flask_app import app
#from submodules.RpiBackend.app import main as localserv
from getmac import get_mac_address as gma

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
        if(True):
            print("1")
            try:
                with open(project_device_path) as project_device_path_file:
                    project_cfg = json.load(project_device_path_file)
                    print("2")
                #project_file = {'document' : open(project_device_path,'rb')}
                #url = "https://app.enercog.com//ui/customer/project/create-project-device"
                url = "https://app.enercog.com//api/no-auth/sm/health-check"
                session = requests.Session()
                print("3")
                retries = Retry(
                    total=5,
                    backoff_factor=1,
                    status_forcelist=[500, 502, 503, 504],
                    allowed_methods=["GET"]
                )
                adapter = HTTPAdapter(max_retries=retries)
                session.mount("https://", adapter)
                session.mount("http://", adapter)

                response = session.post(url=url, json=project_cfg, verify=False)
                #response = session.post(url=url,  verify=False)
                print(f"Response status: {response.status_code}")
                print(f"Response body: {response.text}")

                install_file = True

            except Exception as e:
                print(f"Unexpected error: {e}")


    with open(install_file_path) as installer_file:
        installer_cfg = json.load(installer_file)
    #ctrl.vpp_id = installer_cfg['VPP ID']
    ctrl.site_id = installer_cfg["site id"]
    #ctrl.mqtt_ip = installer_cfg['mqtt server']
    ctrl.controller_id = str(gma())

    global number_of_devices
    number_of_devices = len(installer_cfg["device_list"])
    print('Number of devices is',number_of_devices)
    i=-1
    for device in installer_cfg["device_list"]:
        i+=1
        #ctrl.device_list.append(ctrl.systemDevice(ctrl.deviceType_l2e[device['device_type']],ctrl.commType_l2e[device['comm_type']]))
        for x in device:
            print(x)
            
        device_id = device["device_id"]
        print(device['phases'])  
        num_phases = eval(device['num_phases'])
        
        phase = [int(s) for s in device["phases"].split(',')]
        if("rated_power" in device):
            rated_power  = eval(device['rated_power'])
        else:
            rated_power = 125000
        if("storage_capacity" in device):
            storage_capacity = eval(device['storage_capacity'])
        else:
            storage_capacity = 0

        if(device['comm_type']== 'modbus-tcp'):
            devicetype = ctrl.deviceType_l2e[device['device_type']]
            tcp_details = device['modbus_tcp_details']
            ip = tcp_details['IP']
            read_map = {}   
            ctrl_map={}
            getAddrMapFromPartNum(device["part_num"],read_map,ctrl_map)
            
            if('slave_id' in tcp_details):
                slave_id = eval(tcp_details['slave_id'])
            else:
                slave_id = 1
            scales={}
            ctrl.device_list.append(mbus.modbusTCPDevice(devicetype, ctrl.commType.modbus_tcp,ip,port=eval(tcp_details['port']),slave_id=slave_id,address_map=read_map,ctrl_map=ctrl_map,cfg=device))
            
            #ctrl.device_list[-power = device['rated_power']
            #ctrl.device_list.append(mbus.modbusTCPDevice(devicetype, ctrl.commType.modbus_tcp,ip,port=prt,address_map=addr_map))
            #auto_cfg.createSunsAddrMap(ctrl.device_list[-1].mbus_client,ctrl.device_list[-1].)
            #modbus_tcp_device_list.append(device)
            #print(device)
            #tcp_details = device['modbus-tcp_details']
            #mbus.init_device(mbus.partNumberToddressMap(tcp_details['part_num']),mbus.power_direction.out,tcp_details['IP'],tcp_details['port'] )

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
            #addr_map = mbus.partNumberToddressMap(rtu_details['part_num'])
            scales={}
            ctrl.device_list.append(mbus.modbusRTUDevice(devicetype,ctrl.commType.modbus_rtu,read_map,ctrl_map,port,parity,stop_bits,baud,slave_id,cfg=device))
            

        elif(device['comm_type'] == 'none'):
            ctrl.device_list.append(ctrl.systemDevice(devicetype=ctrl.deviceType.DG,commtype=ctrl.commType.none))

            #print(addr_map)
            #print(scales)
            #addr_ref = auto_cfg.checkPartNumModbus(ctrl.device_list[-1].mbus_client,part_num=rtu_details['part_num'])
            #print(addr_ref)
            #auto_cfg.createSunsAddrMap(ctrl.device_list[-1].mbus_client,ctrl.device_list[-1].modbusRTU_comm_details.address_map,addr_ref[1])
        ctrl.device_list[-1].device_id = device_id
        ctrl.device_list[-1].num_phases = num_phases
        ctrl.device_list[-1].createMeasureRegisterMap()
        ctrl.device_list[-1].createControlRegisterMap()
        ctrl.device_list[-1].phase = phase
        ctrl.device_list[-1].rated_power = rated_power
        ctrl.device_list[-1].storage_capacity = storage_capacity
        if("rated_power") in device:
            ctrl.device_list[-1].rated_power = eval(device["rated_power"])
        if("connected_to" in device):
            ctrl.device_list[-1].connected_to = ctrl.deviceType_l2e[device["connected_to"]]
        if("dg_lim" in device):
            ctrl.device_list[-1].minimum_limit = eval(device["dg_lim"])
        
    print("maps are : ")

    site_response = requests.Response()
    for device in ctrl.device_list:
        print(device.addr_map,device.device_id,device.device_type)
    with open(path_config.path_cfg.base_path + "status_cfg.json") as status_file:
        status_cfg = json.load(status_file)
        print("site create : ",status_cfg["site_created"])
        if(not eval(status_cfg["site_created"])):
            #create site
            with open(project_device_path) as project_device_file:
                site_device_cfg = json.load(project_device_file)
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

    while( not os.path.exists(path_config.path_cfg.base_path + "devices.json")):
        install_file = False
            #print("no file")
        pass
    install_file = True

    while(install_file):
        with open(path_config.path_cfg.base_path + "reports_handling/report_cfg.json") as report_file:
            report_cfg = json.load(report_file)

        read_period = report_cfg["reading_period"] 
        for device in ctrl.device_list:
            try:
                if(device.comm_type == ctrl.commType.modbus_tcp or device.comm_type == ctrl.commType.modbus_rtu):
                    device.decodeData(mbus.getModbusData(device))
            #    elif(device.comm_type == ctrl.commType.gpio):
            #        io.ioDevice.decodeIOData()

            except Exception as e:
                pass
                print(e)

                

        
        rpthndler.data_handler.aggData(ctrl.getAllData())
#        ctrl.runSysControlLoop()
#        rpthndler.data_handler.runDataLoop()
        time.sleep(read_period)

#print("run the file")

def triggerThreads():
    #t1 = threading.Thread(target=getData)
    #t2 = theading.Thread(target=rpthndler.data_handler.runDataLoop)
    #t1.start()
    #t2.start()
    global install_file
    install_file = False

if __name__ == "__main__":

    print("run file")
    path_config.path_cfg = path_config.pathConfig()

    while(not install_file):
        readDeviceList()
        pass


    rpthndler.data_handler = rpthndler.dataBank()

        
    #getData()
    t1 = threading.Thread(target=getData)
    t2 = threading.Thread(target=rpthndler.data_handler.runDataLoop)
    #tmqtt = threading.Thread(target=subscribe.start_subscriber)
    #t3 = threading.Thread(target=localserv.runThread)

    t1.start()
    t2.start()
    #tmqtt.start()
    #t3.start()

    t1.join()
    t2.join()
    #tmqtt.join()
    #t3.join()
    print("thread started")
