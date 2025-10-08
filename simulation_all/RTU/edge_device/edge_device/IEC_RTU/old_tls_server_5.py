import c104
import time
import sys
import json
import threading
from pathlib import Path
from flask import Flask, request, jsonify

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
import path_config

# --- GLOBAL STATE ---
server: c104.Server = None
station: c104.Station = None
vals: dict = {}
points_created = False
server_lock = threading.Lock()
first_data_received = threading.Event()

# --- FLASK APP FOR DATA RECEPTION ---
flask_app = Flask(__name__)

@flask_app.route('/update_data', methods=['POST'])
def update_data_endpoint():
    """Receives data from the main firmware process and updates the server's state."""
    global vals
    if not request.json:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400
    
    with server_lock:
        vals = request.json
    
    if not first_data_received.is_set():
        first_data_received.set() # Signal that the first data packet has arrived
        
    return jsonify({"status": "success"}), 200

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

def create_points_dynamically(initial_data):
    """Creates all IEC-104 points based on the first data snapshot."""
    global station, points_created
    with server_lock:
        if points_created: return
        print("\n--- [IEC Server] First data received. Creating points from structure... ---")
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
        print(f"--- Point creation complete. Map saved to {map_file_path} ---\n")
        points_created = True

def main():
    global server, station
    # Initialize mock path_config for standalone execution
    if 'path_config' not in sys.modules or not hasattr(path_config, 'path_cfg'):
        class MockPathConfig:
            def __init__(self): self.base_path = str(Path(__file__).parent.parent) + "/"
        path_config.path_cfg = MockPathConfig()
    
    # Start the Flask data receiver in a background thread
    flask_thread = threading.Thread(target=lambda: flask_app.run(host='127.0.0.1', port=5001), daemon=True)
    flask_thread.start()
    print("--- [IEC Server] Data receiver started at http://127.0.0.1:5001/update_data ---")
    print("--- [IEC Server] Waiting for the first data packet from the firmware... ---")
    
    # Wait until the first data packet is received before starting the IEC server
    first_data_received.wait()
    
    tls_settings = get_server_tls_config()
    if not tls_settings:
        print("--- [IEC Server] CRITICAL: Could not load TLS settings. Exiting. ---")
        return

    server = c104.Server(transport_security=tls_settings)
    station = server.add_station(common_address=3000)
    
    # Create points using the first received data packet
    create_points_dynamically(vals)

    server.start()
    print("--- [IEC Server] Secure IEC-104 service is now running with TLS. ---")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n--- [IEC Server] Shutting down... ---")
        if server and server.is_running:
            server.stop()

if __name__ == "__main__":
    main()
