import json
from simple_term_menu import TerminalMenu

path = "installer_cfg/installer_cfg.json"
def run_installer_cfg():


    installer_name = input('Please enter installer name : ')

    device_num = eval(input('please enter the number of devices : '))

    vpp_id = eval(input('VPP ID : '))
    site_id = eval(input('site ID : '))
    device_types =["solar-inverter", "battery", "Current transducer", "meter"]
    comm_types = ["modbus-tcp", "modbus-rtu", "CAN", "Analog Input"]

    cfg_details = {}
    cfg_details["installer"]=installer_name
    cfg_details["number_of_devices"]=device_num
    cfg_details["VPP ID"] = vpp_id
    cfg_details["site id"] = site_id
    cfg_details["device_list"]=[]

    for i in range(device_num):
        device = {}
        device["device ID"] = input("Device id : ")
        device_menu= TerminalMenu(device_types,title='Enter device type for device '+str(i+1))
        menu_num=device_menu.show()
        device["device_type"] = device_types[menu_num]

        comm_menu = TerminalMenu(comm_types,title='Enter communication for device ' + str(i+1))
        menu_num=comm_menu.show()
        device["comm_type"] = comm_types[menu_num]
        if(device["comm_type"] == "modbus-tcp"):
            device["modbus-tcp_details"]={}
            device["modbus-tcp_details"]["IP"]=input('enter device IP : ')
            device["modbus-tcp_details"]["port"]=input('enter port number : ')
            device["modbus-tcp_details"]["part_num"]=input('enter part no. : ')

        if(device["comm_type"] == "modbus-rtu"):
            device["modbus-rtu_details"] = {}
            device["modbus-rtu_details"]["part_num"] = input("part number : ")
            device["modbus-rtu_details"]["port"]=input('COMM PORT : ')
            device["modbus-rtu_details"]["stop_bits"]=input('stop bits : ')
            device["modbus-rtu_details"]["parity"]=input('parity : ')
            device["modbus-rtu_details"]["baudrate"]=input('baudrate : ')
            device["modbus-rtu_details"]["slave_id"]=input('slave id : ')


        cfg_details["device_list"].append(device)

    with open(path,'w') as cfgfile:
        json.dump(cfg_details,cfgfile)


    print(cfg_details)

if(__name__ == '__main__'):
    path = "installer_cfg.json"
    run_installer_cfg()