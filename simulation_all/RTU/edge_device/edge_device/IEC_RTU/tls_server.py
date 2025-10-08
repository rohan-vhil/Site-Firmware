import c104
import time
import sys
import json
import threading
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
import path_config

# --- GLOBAL STATE ---
server: c104.Server = None
station: c104.Station = None
vals: dict = {}
server_lock = threading.Lock()

# --- TLS & IEC 104 LOGIC ---
def get_server_tls_config():
    """Configures and returns the TLS settings."""
    ROOT_CERTS_DIR = Path(__file__).parent.parent / 'tests' / 'certs'
    try:
        tlsconf = c104.TransportSecurity(validate=False, only_known=False)
        tlsconf.set_certificate(cert=str(ROOT_CERTS_DIR / "server.cer"), key=str(ROOT_CERTS_DIR / "server-key.pem"))
        tlsconf.set_ca_certificate(cert=str(ROOT_CERTS_DIR / "root.cer"))
        tlsconf.add_allowed_remote_certificate(cert=str(ROOT_CERTS_DIR / "client1.cer"))
        tlsconf.set_version(min=c104.TlsVersion.TLS_1_2, max=c104.TlsVersion.TLS_1_3)
        print(f"[TLS Config] Server TLS configuration loaded successfully from: {ROOT_CERTS_DIR}")
        return tlsconf
    except FileNotFoundError as e:
        print(f"[TLS Config] ERROR: Certificate file not found - {e}.")
        return None

def ReaderFunc(device_id, param_name):
    """Creates a callback function to read a specific data point's value."""
    def dataReader(point: c104.Point) -> None:
        try:
            with server_lock:
                point.value = float(vals.get(str(device_id), {}).get(param_name, 0.0))
        except (ValueError, TypeError):
            point.value = 0.0
    return dataReader

def _create_points_from_initial_data(initial_data):
    """Internal function to create all IEC-104 points based on a data snapshot."""
    global station
    print("\n--- [IEC Server] Pre-creating points from initial data structure... ---")
    point_map = {}
    io_address_counter = 3001
    
    for device_id, params in sorted(initial_data.items()):
        if isinstance(params, dict):
            for param_name, value in sorted(params.items()):
                if isinstance(value, (int, float)):
                    func_name = f"ReaderFunc_{device_id.replace(':', '_')}_{param_name}"
                    globals()[func_name] = ReaderFunc(device_id, param_name)
                    
                    point = station.add_point(io_address=io_address_counter, type=c104.Type.M_ME_NC_1)
                    point.on_before_read(callable=globals()[func_name])
                    
                    point_map[io_address_counter] = {"device_id": device_id, "parameter": param_name}
                    print(f"  -> Mapped IOA {io_address_counter} to '{device_id} -> {param_name}'")
                    io_address_counter += 1
    
    map_file_path = path_config.path_cfg.base_path + "IEC_RTU/IEC_point_map.json"
    with open(map_file_path, 'w') as f: json.dump(point_map, f, indent=4)
    print(f"--- Point pre-creation complete. Map saved to {map_file_path} ---\n")

def initializeIECServer(initial_data):
    """
    Initializes the server instance, station, and all data points BEFORE the server starts.
    This is called once by main_thread.py.
    """
    global server, station
    
    tls_settings = get_server_tls_config()
    if not tls_settings:
        print("--- [IEC Server] CRITICAL: Could not load TLS settings. Server cannot be initialized. ---")
        return

    server = c104.Server(transport_security=tls_settings)
    station = server.add_station(common_address=3000)
    
    if initial_data:
        _create_points_from_initial_data(initial_data)
    else:
        print("--- [IEC Server] WARNING: No initial data provided. Server will start without any points. ---")

def runServer(data_handler_object):
    """
    This is the target function for the server thread. It starts the pre-configured server
    and then enters a loop to continuously update its internal data.
    """
    global server, vals
    if not server:
        print("--- [IEC Server] ERROR: Server was not initialized before runServer was called. Aborting thread. ---")
        return
        
    # Start the server to begin listening for client connections
    server.start()
    print("--- [IEC Server] Secure IEC-104 service is now running with TLS. ---")
    
    # Loop to keep the server's data fresh
    while True:
        current_data = getattr(data_handler_object, 'avg_data', None)
        if current_data:
            with server_lock:
                vals = current_data.copy()
        
        time.sleep(1) # Update internal values every second
