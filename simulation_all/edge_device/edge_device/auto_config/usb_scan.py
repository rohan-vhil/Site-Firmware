import os
import sys
from pymodbus.client import ModbusTcpClient
from pymodbus.client import ModbusSerialClient
from pymodbus import framer
from dataclasses import dataclass

sys.path.insert(0,"/dev")
path = "/dev/serial/by-id/"
#files = [x for x in os.listdir(path)]
files = os.listdir(path)


print(files)


bauds = [9600,4800,19200]
num_devices = 1
paritys = ['N','E','O']
slaves = [1,2,3,4,5]
@dataclass
class modbusDEvice:
    port :str
    baud : int
    parity:str
    slave_id : int

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