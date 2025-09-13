import c104
import random
import time
import sys
sys.path.insert(0,"../")
import path_config
import json
import inspect

# --- UNCHANGED HELPER FUNCTIONS ---

def on_step_command(point: c104.Point, previous_info: c104.Information, message: c104.IncomingMessage) -> c104.ResponseState:
    print(f"{point.type} STEP COMMAND on IOA: {point.io_address}, message: {message}")
    return c104.ResponseState.SUCCESS

def ReaderFunc(device_id, param_name):
    def dataReader(point: c104.Point) -> None:
        try:
            # This is the core lookup logic
            point.value = float(vals[str(device_id)][param_name])
            print(f"SUCCESS -> Reading for IOA {point.io_address} ({device_id} | {param_name}): Found value {point.value}")
        except KeyError:
            # This will catch errors if the device_id or param_name is not in the data
            print(f"ERROR -> Reading for IOA {point.io_address} ({device_id} | {param_name}): Key not found.")
        except Exception as e:
            # This will catch other errors, like if the value isn't a number
            print(f"ERROR -> Reading for IOA {point.io_address} ({device_id} | {param_name}): {e}")
    return dataReader

# --- GLOBAL VARIABLES ---
server: c104.Server
vals: dict = {} # Initialize as an empty dictionary

# --- CORRECTED SERVER INITIALIZATION LOGIC ---
def startIECServer():
    global server
    server = c104.Server()

    try:
        with open(path_config.path_cfg.base_path + "IEC_RTU/RTU_addr_config.json") as rtu_file:
            rtu_json = json.load(rtu_file)
    except FileNotFoundError:
        print("ERROR: RTU_addr_config.json not found!")
        return
    except json.JSONDecodeError:
        print("ERROR: RTU_addr_config.json is not valid JSON!")
        return

    station = server.add_station(common_address=3000)
    
    # Process Analog Signals
    io_address_counter = rtu_json["analog_signals"]["start_address"]
    for device in rtu_json["analog_signals"]["devices"]:
        if "firmware_device_id" not in device:
            print(f"WARNING: Skipping device '{device.get('device_name')}' because it's missing 'firmware_device_id'.")
            continue

        firmware_id = device["firmware_device_id"]

        for data_object in device["data_objects"]:
            param_name = data_object["name"]
            
            # Create a unique function name to avoid conflicts in globals()
            func_name = f"ReaderFunc_{firmware_id.replace(':', '_')}_{param_name}"
            
            # Create the reader function, passing the correct firmware ID and parameter name
            globals()[func_name] = ReaderFunc(firmware_id, param_name)
            
            print(f"Creating point for '{firmware_id} -> {param_name}' at IOA {io_address_counter}")
            
            # Add the point to the IEC station
            point = station.add_point(io_address=io_address_counter, type=getattr(c104.Type, data_object["type"]))
            point.on_before_read(callable=globals()[func_name])
             
            io_address_counter += 1 # Increment for the next data point
            
    server.start()

# --- CORRECTED SERVER RUN LOOP (FIXES RACE CONDITION) ---
def runServer(val):
    global vals
    while(1):
        # Only update the global 'vals' if the received dictionary is not empty
        if val:
            vals = val
        
        # This print statement will show you the exact dictionary the server is working with
        print("\n--- [IEC Server] Current data ---")
        print(vals)
        print("---------------------------------\n")
        
        time.sleep(5)

# This main block is for standalone testing and is not used when run from main_thread.py
def main():
    print("This script is intended to be run as a thread from main_thread.py, not standalone.")

if __name__ == "__main__":
    main()
