import os
import sys
from pymodbus.client import ModbusTcpClient
from pymodbus.client import ModbusSerialClient
from pymodbus import framer
from dataclasses import dataclass
import json
import time
sys.path.insert(0,"../")

sys.path.insert(0,"/dev")
path = "/dev/serial/by-id/"
#files = [x for x in os.listdir(path)]
files = os.listdir(path)


print(files)


bauds =[4800,9600,19200]
num_devices = 1
paritys = ['N','E','O']
slaves = [1,2,3,4,5]
@dataclass
class modbusDEvice:
    port :str
    baud : int
    parity:str
    slave_id : int

"""
device_list = []
for file in files:

    for baud in bauds:
        for parity in paritys:
            for slave in slaves:
                client = ModbusSerialClient(port = path + file,baudrate=baud,parity=parity,framer=framer.FramerType.RTU)
                print(path+file,baud,parity,slave)
                #client.close()
                if(client.connect()):
                    print("connected")
                        #print("connected + ")
                    try:
                        regs = client.read_input_registers(address=1,count=1,slave=slave)
                        print("got response : ",regs.registers,file,slave)
                        if(not regs.isError()):
                                device_list.append(modbusDEvice(path+file,baud,parity))
                        else:
                            print("error")

                    except Exception as e:
                        pass
                        #print("exception : ",e)
                else:
                     print("could not connect to")
                client.close()

print(device_list)
"""

def detectPort(files,device):
    for file in files:
        for baud in bauds:
            for par in paritys:
                client = ModbusSerialClient(port = path + file,baudrate=baud,parity=par,framer=framer.FramerType.RTU)
                for slave in slaves:
                    #iterate through all possibilities
                    
                    if(client.connect()):
                        #connection on port
                        try:
                            #regs = client.read_input_registers(address=1,count=1,slave=slave)
                            #print(regs)
                            
                                #since we are able to connect and read , let's identify the part
                            if(verifyPart(client,device,slave)):
                                print("growwatt inverter at here",file,baud,par,slave)
                                return
                            pass
                        except Exception as e:
                            pass
                    else:
                        print("nothing on port")
                    client.close()
                    time.sleep(1)
                del client



def verifyPart(client : ModbusSerialClient | ModbusTcpClient, part,slave):
    #read voltages
    frequency_found = False
    regs = client.read_input_registers(address=37,slave=slave)
    if(not regs.isError()):
        print(regs.registers)
        if(regs.registers[0] < (50 + 1) *100 and regs.registers[0] > (50 - 1) *100):
            frequency_found = True
    else :
        print("error",client.comm_params,slave)
        return False

    voltage_found = False
    regs = client.read_input_registers(address=38,count=1,slave=slave)
    if(not regs.isError()):
        print(regs.registers)
        if(regs.registers[0] < 3000 and regs.registers[0] > 2000):
            voltage_found = True

    return frequency_found & voltage_found



    
    


def detectPart(client : ModbusTcpClient | ModbusSerialClient):
    with open("auto_config.json") as cfg_file:
        cfg = json.load(cfg_file)
    print(cfg)
    device_connected = client.connect()

    got_device = False
    for device in cfg["modbus"]:
        for sets in cfg["modbus"][device] :
            if("holding" in cfg["modbus"][device][sets]):
                for regs in cfg["modbus"][device][sets]["holding"]:
                    try :
                        #client.read_holding_registers(int(regs),1)
                        read_regs = client.read_holding_registers(address=int(regs),count=1)
                        if(read_regs.registers[0] == int(cfg["modbus"][device][sets]["holding"][regs])):
                            got_device = True
                        else:
                            print(read_regs,regs)
                            got_device = False
                    except Exception as e:
                        print(e,regs)
                        got_device = False

            if("input" in cfg["modbus"][device][sets]):
                for regs in cfg["modbus"][device][sets]["input"]:
                    try :
                        client.read_holding_registers(int(regs),1)
                        read_regs = client.read_input_registers(int(regs),1)
                        if(read_regs.registers[0] == cfg["modbus"][device][sets]["input"][regs]):
                            got_device = True
                        else:
                            got_device = False

                    except Exception:
                        got_device = False

            if(got_device == True):
                    return device


                        
                            



            pass
client = ModbusTcpClient('0.0.0.0',port=505)
print(detectPort(files,"growatt"))