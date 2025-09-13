from pymodbus.client import ModbusSerialClient
from pymodbus import framer
import sys
import time

rtu_port = '/dev/ttyUSB0'

rtu_client = ModbusSerialClient(
    port=rtu_port,
    framer=framer.FramerType.RTU,
    baudrate=9600,
    timeout=3,
    parity='N'
)

rtu_client.connect()

if rtu_client.connect():
   
    print(f"Connection Successful")
    #rtu_client.write_register(address=3, value=100, slave=1)
    while True:
        data = rtu_client.read_input_registers(address=49151,count=5,slave=7)

        if data.isError():
            print("reading error")
        else:
            print("data : ", data.registers)
            print()
            time.sleep(1)

    rtu_client.close()
else:
    print(f"Connection Failed")
