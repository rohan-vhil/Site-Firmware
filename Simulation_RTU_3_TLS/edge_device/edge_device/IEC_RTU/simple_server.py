import c104
import time
import sys
import json
import threading
import requests

sys.path.insert(0,"../")
import path_config

# --- CONFIGURATION ---
DUMMY_PUBLISH_URL = "http://127.0.0.1:5000/publish"
PUBLISH_INTERVAL_SECONDS = 10 # How often to send data to the dummy URL

# --- GLOBAL VARIABLES ---
server: c104.Server
station: c104.Station
vals: dict = {}
points_created = False

# --- HELPER FUNCTION ---
def ReaderFunc(device_id, param_name):
    def dataReader(point: c104.Point) -> None:
        try:
            point.value = float(vals[str(device_id)][param_name])
        except (KeyError, TypeError):
            pass
    return dataReader

# --- DYNAMIC POINT CREATION ---
def create_dynamic_points(data):
    global station
    print("\n--- [IEC Server] First data packet received. Creating points dynamically... ---")
    point_map = {}
    io_address_counter = 3001
    sorted_devices = sorted(data.items())
    for device_id, params in sorted_devices:
        if not isinstance(params, dict):
            continue
        sorted_params = sorted(params.items())
        for param_name, value in sorted_params:
            if isinstance(value, (int, float)):
                func_name = f"ReaderFunc_{device_id.replace(':', '_')}_{param_name}"
                globals()[func_name] = ReaderFunc(device_id, param_name)
                point = station.add_point(io_address=io_address_counter, type=c104.Type.M_ME_NC_1)
                point.on_before_read(callable=globals()[func_name])
                point_map[io_address_counter] = {"device_id": device_id, "parameter": param_name}
                print(f"  -> Mapped IOA {io_address_counter} to '{device_id} -> {param_name}'")
                io_address_counter += 1
    map_file_path = path_config.path_cfg.base_path + "IEC_RTU/IEC_point_map.json"
    with open(map_file_path, 'w') as f:
        json.dump(point_map, f, indent=4)
    print(f"--- Dynamic point creation complete. Map saved to {map_file_path} ---\n")

# --- NEW: DATA PUBLISHING THREAD ---
def publish_data_periodically():
    """This function runs in a background thread and sends data to the dummy URL."""
    while True:
        time.sleep(PUBLISH_INTERVAL_SECONDS)
        
        if vals: # Check if there is data to send
            try:
                # Make a thread-safe copy of the data
                data_to_send = vals.copy()
                response = requests.post(DUMMY_PUBLISH_URL, json=data_to_send, timeout=5)
                if response.status_code == 200:
                    print(f"--- [IEC Server] Successfully published data to {DUMMY_PUBLISH_URL} ---")
                else:
                    print(f"--- [IEC Server] WARN: Failed to publish data. Status: {response.status_code} ---")
            except requests.exceptions.RequestException as e:
                print(f"--- [IEC Server] ERROR: Could not connect to dummy receiver at {DUMMY_PUBLISH_URL} ---")

# --- SERVER INITIALIZATION & RUN LOOP ---
def startIECServer():
    global server, station
    server = c104.Server()
    station = server.add_station(common_address=3000)
    server.start()
    
    # Start the new background thread for publishing data
    publisher_thread = threading.Thread(target=publish_data_periodically, daemon=True)
    publisher_thread.start()
    
    print("--- [IEC Server] Started. IEC-104 service is running. ---")
    print(f"--- [IEC Server] Now also publishing data every {PUBLISH_INTERVAL_SECONDS}s to {DUMMY_PUBLISH_URL} ---")

def runServer(data_handler_object):
    global vals, points_created
    while(1):
        current_data = data_handler_object.avg_data
        if current_data:
            vals = current_data.copy()
        if not points_created and vals:
            create_dynamic_points(vals)
            points_created = True
        time.sleep(5)

if __name__ == "__main__":
    print("This script is intended to be run as a thread from main_thread.py, not standalone.")
