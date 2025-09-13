from pymodbus import framer
from pymodbus.client import ModbusTcpClient,ModbusSerialClient
from pymodbus.client import ModbusBaseClient as cltlib

ip='0.0.0.0'
port = 504
slave_id=2

rtu_port = '/dev/pts/8'


tcp_client = ModbusTcpClient(ip,port=port)
rtu_client = ModbusSerialClient(port=rtu_port,framer=framer.FramerType.RTU,baudrate=9600,timeout=3)

print(tcp_client.connect())

read_Data =tcp_client.read_input_registers(address=19026,count=10,slave=1)
print(read_Data.registers)

    



