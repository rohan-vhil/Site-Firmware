import time
import random
import logging
import threading
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian

# --- Configuration ---
# Set the IP address and port for the Modbus TCP server.
# Use '0.0.0.0' to allow connections from other machines on your network.
HOST_IP = "0.0.0.0"
SERVER_PORT = 5020
SLAVE_ID = 0x01

# Define the starting address for the total_power register.
# We will use a 32-bit integer, so it will occupy 2 consecutive 16-bit registers.
TOTAL_POWER_REGISTER_ADDR = 100

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()


def update_power_value(context):
    """
    A worker process that runs in the background to update the total_power
    value with a random number every few seconds.
    """
    log.info("Starting background thread to update power values.")
    
    while True:
        try:
            # 1. Generate a random power value between 1000W and 5000W
            power_value = random.randint(1000, 5000)
            
            # 2. Build the 32-bit integer payload. This ensures the master
            #    can read it correctly. The byte and word order should match
            #    what the master expects.
            builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.BIG)
            builder.add_32bit_int(power_value)
            payload = builder.to_registers()

            # 3. Get the slave context and set the register values.
            #    Function code 3 corresponds to Holding Registers.
            slave_context = context[SLAVE_ID]
            slave_context.set_values(3, TOTAL_POWER_REGISTER_ADDR, payload)

            log.info(f"Updated simulated load power (register {TOTAL_POWER_REGISTER_ADDR}) to: {power_value} W")

            # 4. Wait for 5 seconds before the next update
            time.sleep(5)

        except Exception as e:
            log.error(f"Error in update thread: {e}")
            break
            
    log.info("Stopping background update thread.")


def run_meter_simulator():
    """
    Sets up and runs the Modbus TCP server.
    """
    # Create the data store for the server. We need at least 102 registers
    # to accommodate the power value at address 100.
    data_block = ModbusSequentialDataBlock(0, [0] * 200)
    
    # Create the slave context, assigning the data block to our slave ID.
    slave_store = {
        SLAVE_ID: ModbusSlaveContext(
            di=None, co=None, hr=data_block, ir=None
        ),
    }

    server_context = ModbusServerContext(slaves=slave_store, single=False)

    # Start the background thread to update the power value.
    update_thread = threading.Thread(target=update_power_value, args=(slave_store,), daemon=True)
    update_thread.start()

    # Start the Modbus TCP server.
    log.info(f"Starting Modbus TCP Meter Simulator on {HOST_IP}:{SERVER_PORT}")
    StartTcpServer(context=server_context, address=(HOST_IP, SERVER_PORT))


if __name__ == "__main__":
    run_meter_simulator()
