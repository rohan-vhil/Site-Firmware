from pymodbus import framer
from pymodbus.client import ModbusTcpClient,ModbusSerialClient
from pymodbus.client import ModbusBaseClient as cltlib

ip='127.0.0.1'
port = 505
slave_id=2

rtu_port = '/dev/ttyUSB0'


tcp_client = ModbusTcpClient(ip,port=port)
try :
    rtu_client = ModbusSerialClient(port=rtu_port,framer=framer.FramerType.RTU,baudrate=9600,timeout=1,parity='O')
    print(rtu_client.connect())

except Exception as e:
    print(e)

try:
    read_Data =rtu_client.read_input_registers(address=19001,count=10,slave=1)
    print(read_Data.isError())
    print(read_Data)
    rtu_client.close()
except Exception as e:
    print(e)
#print(read_Data.registers)

    



