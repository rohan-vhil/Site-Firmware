import c104
import random
import time
import sys
sys.path.insert(0,"../")
import path_config
import json
import inspect

# --- GLOBAL VARIABLES ---
server: c104.Server
# This global dictionary will be safely updated by the runServer thread
vals: dict = {}

# --- HELPER FUNCTIONS ---

def ReaderFunc(device_id, param_name):
    def dataReader(point: c104.Point) -> None:
        try:
            # The 'vals' dictionary is a safe copy, so we read from it
            point.value = float(vals[str(device_id)][param_name])
            print(f"SUCCESS -> Reading for IOA {point.io_address} ({device_id} | {param_name}): Found value {point.value}")
        except KeyError:
            print(f"ERROR -> Reading for IOA {point.io_address} ({device_id} | {param_name}): Key not found in vals.")
        except Exception as e:
            print(f"ERROR -> Reading for IOA {point.io_address} ({device_id} | {param_name}): {e}")
    return dataReader

# --- SERVER INITIALIZATION LOGIC ---
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
    
    io_address_counter = rtu_json["analog_signals"]["start_address"]
    for device in rtu_json["analog_signals"]["devices"]:
        if "firmware_device_id" not in device:
            print(f"WARNING: Skipping device '{device.get('device_name')}' because it's missing 'firmware_device_id'.")
            continue

        firmware_id = device["firmware_device_id"]

        for data_object in device["data_objects"]:
            param_name = data_object["name"]
            func_name = f"ReaderFunc_{firmware_id.replace(':', '_')}_{param_name}"
            globals()[func_name] = ReaderFunc(firmware_id, param_name)
            
            print(f"Creating point for '{firmware_id} -> {param_name}' at IOA {io_address_counter}")
            
            point = station.add_point(io_address=io_address_counter, type=getattr(c104.Type, data_object["type"]))
            point.on_before_read(callable=globals()[func_name])
             
            io_address_counter += 1
            
    server.start()

# --- FINAL CORRECTED SERVER RUN LOOP ---
def runServer(data_handler_object):
    global vals
    while(1):
        # Access the dictionary from the object inside the loop
        # This ensures we always have the latest data
        current_data = data_handler_object.avg_data

        if current_data:
            # Make a thread-safe copy for the reader functions to use
            vals = current_data.copy()

        print("\n--- [IEC Server] Current data ---")
        print(vals)
        print("---------------------------------\n")
        
        time.sleep(5)

# This main block is for standalone testing
def main():
    print("This script is intended to be run as a thread from main_thread.py, not standalone.")

if __name__ == "__main__":
    main()
