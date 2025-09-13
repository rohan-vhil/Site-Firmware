import time
import logging
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

# --- Configuration ---

# -- Meter Simulator (TCP) Configuration --
# IP address of the machine running meter_simulator.py
METER_IP = 'localhost'  # Change to the actual IP if running on another machine
METER_PORT = 5020
METER_SLAVE_ID = 1
METER_POWER_ADDR = 100 # Address of the power reading on the meter

# -- Real Inverter (RTU) Configuration --
# The serial port for your RS485-to-USB converter on the Raspberry Pi.
# It's usually '/dev/ttyUSB0' or '/dev/ttyAMA0'.
INVERTER_SERIAL_PORT = '/dev/ttyUSB0'
INVERTER_SLAVE_ID = 1
INVERTER_BAUDRATE = 9600
# The holding register on your inverter to control power output percentage.
INVERTER_POWER_CTRL_ADDR = 3
# The rated power of your inverter in Watts. This is crucial for calculating the percentage.
INVERTER_RATED_POWER_W = 5000 # Example: 5kW inverter

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

def run_zero_export_control():
    """
    Main control loop to read from the meter and write to the inverter.
    """
    log.info("Starting Zero-Export Controller.")
    
    # Initialize clients. They will be connected/closed inside the loop.
    meter_client = ModbusTcpClient(METER_IP, port=METER_PORT)
    inverter_client = ModbusSerialClient(
        port=INVERTER_SERIAL_PORT,
        baudrate=INVERTER_BAUDRATE,
        parity='N',
        stopbits=1,
        bytesize=8,
        timeout=1
    )

    while True:
        try:
            # --- Step 1: Read Load Power from Meter Simulator ---
            log.info(f"Attempting to connect to meter at {METER_IP}:{METER_PORT}...")
            if not meter_client.connect():
                log.error("Could not connect to meter simulator. Retrying...")
                time.sleep(5)
                continue

            # Read 2 consecutive holding registers starting from METER_POWER_ADDR
            result = meter_client.read_holding_registers(
                address=METER_POWER_ADDR,
                count=2,
                slave=METER_SLAVE_ID
            )
            
            if result.isError():
                log.error(f"Failed to read from meter: {result}")
                meter_client.close()
                time.sleep(5)
                continue

            # Decode the 32-bit integer value from the registers
            decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.BIG, wordorder=Endian.BIG)
            load_power_watts = decoder.decode_32bit_int()
            log.info(f"Successfully read load power: {load_power_watts} W")
            meter_client.close()

            # --- Step 2: Calculate Inverter Setpoint for Zero Export ---
            # For basic zero export, inverter power should match the load.
            inverter_setpoint_watts = load_power_watts
            
            # Convert the Watt setpoint to a percentage of the inverter's rated power
            power_setpoint_percent = (inverter_setpoint_watts / INVERTER_RATED_POWER_W) * 100
            
            # Clamp the value between 0% and 100% to prevent errors
            power_setpoint_percent = max(0, min(100, power_setpoint_percent))
            
            # We need to write an integer value to the register
            power_setpoint_register_value = int(power_setpoint_percent)
            log.info(f"Calculated Inverter Setpoint: {power_setpoint_percent:.2f}% ({power_setpoint_register_value})")

            # --- Step 3: Write Setpoint to Real Inverter ---
            log.info(f"Attempting to connect to inverter on {INVERTER_SERIAL_PORT}...")
            if not inverter_client.connect():
                log.error("Could not connect to inverter. Check RS485 connection and port.")
                time.sleep(5)
                continue
            
            # Write the calculated percentage to the inverter's control register
            write_result = inverter_client.write_register(
                address=INVERTER_POWER_CTRL_ADDR,
                value=power_setpoint_register_value,
                slave=INVERTER_SLAVE_ID
            )

            if write_result.isError():
                log.error(f"Failed to write to inverter: {write_result}")
            else:
                log.info(f"Successfully wrote {power_setpoint_register_value}% to inverter register {INVERTER_POWER_CTRL_ADDR}")
            
            inverter_client.close()

        except Exception as e:
            log.error(f"An unexpected error occurred in the control loop: {e}")
            # Ensure clients are closed on error
            if meter_client.is_socket_open():
                meter_client.close()
            if inverter_client.is_socket_open():
                inverter_client.close()

        # Wait before starting the next control cycle
        log.info("--- Cycle complete. Waiting 5 seconds. ---")
        time.sleep(5)

if __name__ == "__main__":
    run_zero_export_control()
