import c104
import time
import sys
import json
import threading
import requests
from pathlib import Path

# Assuming path_config is in a location accessible via sys.path
sys.path.insert(0,"../")
import path_config

# --- CONFIGURATION ---
DUMMY_PUBLISH_URL = "http://127.0.0.1:5000/publish"
PUBLISH_INTERVAL_SECONDS = 10

# --- GLOBAL VARIABLES ---
server: c104.Server
station: c104.Station
vals: dict = {}
points_created = False
server_lock = threading.Lock() 

# --- TLS SECURITY CONFIGURATION (UPDATED PATH) ---
def get_server_tls_config():
    """
    Configures and returns the TLS settings for the IEC 104 server.
    This function now points to the correct 'tests/certs' directory.
    """
    # CORRECTED PATH: Navigate from script location up to base project and then to tests/certs
    # Path(__file__).parent -> /IEC_RTU/
    # .parent -> /edge_device/
    # .parent -> /edge_device/ (project root)
    ROOT_CERTS_DIR = Path(__file__).parent.parent / 'tests' / 'certs'
    
    try:
        tlsconf = c104.TransportSecurity(validate=False, only_known=False)
        
        # 1. Set the server's own certificate and private key.
        tlsconf.set_certificate(
            cert=str(ROOT_CERTS_DIR / "server.cer"), 
            key=str(ROOT_CERTS_DIR / "server-key.pem")
        )
        
        # 2. Set the Certificate Authority (CA) certificate to verify clients against.
        tlsconf.set_ca_certificate(cert=str(ROOT_CERTS_DIR / "root.cer"))
        
        # 3. Specify which client certificates are explicitly allowed to connect.
        tlsconf.add_allowed_remote_certificate(cert=str(ROOT_CERTS_DIR / "client1.cer"))

        # 4. Enforce a minimum TLS version for better security.
        tlsconf.set_version(min=c104.TlsVersion.TLS_1_2, max=c104.TlsVersion.TLS_1_3)
        
        print(f"[TLS Config] Server TLS configuration loaded successfully from: {ROOT_CERTS_DIR}")
        return tlsconf
        
    except FileNotFoundError as e:
        print(f"[TLS Config] ERROR: Certificate file not found - {e}. Please ensure the path '{ROOT_CERTS_DIR}' is correct.")
        return None
    except Exception as e:
        print(f"[TLS Config] ERROR: An unexpected error occurred while creating TLS config: {e}")
        return None

# --- HELPER FUNCTION ---
def ReaderFunc(device_id, param_name):
    def dataReader(point: c104.Point) -> None:
        try:
            with server_lock:
                point.value = float(vals.get(str(device_id), {}).get(param_name, 0.0))
        except (ValueError, TypeError):
            point.value = 0.0
    return dataReader

# --- DYNAMIC POINT CREATION ---
def create_dynamic_points(data):
    global station, points_created
    with server_lock:
        if points_created:
            return
            
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
        
        points_created = True
        print(f"--- Dynamic point creation complete. Map saved to {map_file_path} ---\n")

# --- DATA PUBLISHING THREAD ---
def publish_data_periodically():
    while True:
        time.sleep(PUBLISH_INTERVAL_SECONDS)
        
        with server_lock:
            if not vals:
                continue
            data_to_send = vals.copy()

        try:
            response = requests.post(DUMMY_PUBLISH_URL, json=data_to_send, timeout=5)
            if response.status_code == 200:
                print(f"--- [IEC Server] Successfully published data to {DUMMY_PUBLISH_URL} ---")
            else:
                print(f"--- [IEC Server] WARN: Failed to publish data. Status: {response.status_code} ---")
        except requests.exceptions.RequestException:
            print(f"--- [IEC Server] ERROR: Could not connect to data receiver at {DUMMY_PUBLISH_URL} ---")

# --- SERVER INITIALIZATION & RUN LOOP ---
def startIECServer():
    global server, station
    
    tls_settings = get_server_tls_config()
    if not tls_settings:
        print("--- [IEC Server] CRITICAL: Could not load TLS settings. Server will not start. ---")
        return

    server = c104.Server(transport_security=tls_settings)
    station = server.add_station(common_address=3000)
    server.start()
    
    publisher_thread = threading.Thread(target=publish_data_periodically, daemon=True)
    publisher_thread.start()
    
    print("--- [IEC Server] Secure IEC-104 service is running with TLS. ---")
    print(f"--- [IEC Server] Publishing data every {PUBLISH_INTERVAL_SECONDS}s to {DUMMY_PUBLISH_URL} ---")

def runServer(data_handler_object):
    global vals
    while True:
        current_data = getattr(data_handler_object, 'avg_data', None)
        if current_data:
            with server_lock:
                vals = current_data.copy()
            
            if not points_created and vals:
                create_dynamic_points(vals)

        time.sleep(5)

if __name__ == "__main__":
    print("This script is intended to be run as a thread from main_thread.py, not standalone.")
