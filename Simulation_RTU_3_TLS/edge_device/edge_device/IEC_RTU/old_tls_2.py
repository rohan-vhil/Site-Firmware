import c104
import time
import sys
import json
import threading
from pathlib import Path

# Add the parent directory to the path to find the 'path_config' module
sys.path.insert(0, str(Path(__file__).parent.parent))
import path_config

# --- GLOBAL VARIABLES ---
server: c104.Server
station: c104.Station
vals: dict = {}
server_lock = threading.Lock()

# --- TLS SECURITY CONFIGURATION ---
def get_server_tls_config():
    """Configures and returns the TLS settings for the IEC 104 server."""
    # Corrected Path: Navigates from this script's location up two levels to the project root,
    # then into the 'tests/certs' directory.
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

# --- HELPER FUNCTION ---
def ReaderFunc(device_id, param_name):
    """Creates a callback function to read a specific data point's value."""
    def dataReader(point: c104.Point) -> None:
        try:
            with server_lock:
                # Safely get the value, defaulting to 0.0 if any key is missing
                point.value = float(vals.get(str(device_id), {}).get(param_name, 0.0))
        except (ValueError, TypeError):
            point.value = 0.0
    return dataReader

# --- DYNAMIC POINT CREATION (PRE-SERVER START) ---
def create_points_from_initial_data(initial_data):
    """Creates all IEC-104 points based on an initial data snapshot."""
    global station
    print("\n--- [IEC Server] Pre-creating points from initial data structure... ---")
    point_map = {}
    io_address_counter = 3001 # Starting Information Object Address
    
    # Sort for consistent IOA mapping between runs
    sorted_devices = sorted(initial_data.items())
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
    
    print(f"--- Point pre-creation complete. Map saved to {map_file_path} ---\n")

# --- SERVER INITIALIZATION & DATA POLLING LOOP ---
def startIECServer(initial_data):
    """Initializes and starts the secure IEC-104 server."""
    global server, station
    
    tls_settings = get_server_tls_config()
    if not tls_settings:
        print("--- [IEC Server] CRITICAL: Could not load TLS settings. Server will not start. ---")
        return

    server = c104.Server(transport_security=tls_settings)
    station = server.add_station(common_address=3000)
    
    # CRITICAL STEP: Create points BEFORE starting the server to avoid race conditions
    if initial_data:
        create_points_from_initial_data(initial_data)
    else:
        print("--- [IEC Server] WARNING: No initial data provided. Server will start without any points. ---")

    server.start()
    print("--- [IEC Server] Secure IEC-104 service is now running with TLS. ---")

def runServer(data_handler_object):
    """
    This function runs as a thread, continuously updating the 'vals' dictionary
    with the latest data from the main firmware's data handler.
    """
    global vals
    while True:
        # Get the latest data from the data handler object
        current_data = getattr(data_handler_object, 'avg_data', None)
        if current_data:
            with server_lock:
                vals = current_data.copy()
        
        time.sleep(1) # Update internal values every second

if __name__ == "__main__":
    print("This script is intended to be run as a thread from main_thread.py, not standalone.")

