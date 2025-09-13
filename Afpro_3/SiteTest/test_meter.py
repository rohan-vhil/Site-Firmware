from pymodbus.client import ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus import framer
import time

def read_and_decode_float(client, address, slave_id):
    result = client.read_holding_registers(address=address, count=2, slave=slave_id)
    if not result.isError():
        decoder = BinaryPayloadDecoder.fromRegisters(
            result.registers,
            byteorder=Endian.BIG,
            wordorder=Endian.BIG
        )
        return decoder.decode_32bit_float()
    else:
        print(f"Error reading address {address}: {result}")
        return None

rtu_port = '/dev/ttyUSB0'

rtu_client = ModbusSerialClient(
    port=rtu_port,
    framer=framer.FramerType.RTU,
    baudrate=9600,
    timeout=3,
    parity='E',
    stopbits=1,
    bytesize=8
)

if rtu_client.connect():
    print("Connection Successful")
    try:
        while True:
            slave_id = 2
            
            curr_a = read_and_decode_float(rtu_client, 2999, slave_id)
            curr_b = read_and_decode_float(rtu_client, 3001, slave_id)
            curr_c = read_and_decode_float(rtu_client, 3003, slave_id)
            curr_n = read_and_decode_float(rtu_client, 3005, slave_id)
            curr_avg = read_and_decode_float(rtu_client, 3009, slave_id)

            v1 = read_and_decode_float(rtu_client, 3027, slave_id)
            v2 = read_and_decode_float(rtu_client, 3029, slave_id)
            v3 = read_and_decode_float(rtu_client, 3031, slave_id)
            vn = read_and_decode_float(rtu_client, 3033, slave_id)

            p1 = read_and_decode_float(rtu_client, 3053, slave_id)
            pt = read_and_decode_float(rtu_client, 3059, slave_id)

            print(f"Current A: {curr_a}")
            print(f"Current B: {curr_b}")
            print(f"Current C: {curr_c}")
            print(f"Current N: {curr_n}")
            print(f"Current Avg: {curr_avg}")
            
            print(f"Voltage L-N 1: {v1}")
            print(f"Voltage L-N 2: {v2}")
            print(f"Voltage L-N 3: {v3}")
            print(f"Voltage L-L Avg: {vn}")

            print(f"Active Power 1: {p1}")
            print(f"Active Power Total: {pt}")
            
            print("\n==============================END===============================\n")
            time.sleep(3)

    except KeyboardInterrupt:
        print("Closing connection...")
    finally:
        rtu_client.close()
else:
    print("Connection Failed")

# Please use "client.convert_from_registers()" or "client.convert_to_registers"'
