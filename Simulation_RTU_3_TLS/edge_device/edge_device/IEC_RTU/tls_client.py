import c104
import time
import json
import threading
from pathlib import Path
import sys

# Add the parent directory to the path to find the 'path_config' module
sys.path.insert(0, str(Path(__file__).parent.parent))
import path_config

# --- GLOBAL VARIABLES ---
client: c104.Client
connection: c104.Connection
station: c104.Station
points_configured = False
client_lock = threading.Lock()

# --- TLS SECURITY CONFIGURATION ---
def get_client_tls_config():
    """Configures and returns the TLS settings for the IEC 104 client."""
    ROOT_CERTS_DIR = Path(__file__).parent.parent / 'tests' / 'certs'
    
    try:
        tlsconf = c104.TransportSecurity(validate=False, only_known=False)
        tlsconf.set_certificate(
            cert=str(ROOT_CERTS_DIR / "client1.cer"), 
            key=str(ROOT_CERTS_DIR / "client1-key.pem")
        )
        tlsconf.set_ca_certificate(cert=str(ROOT_CERTS_DIR / "root.cer"))
        tlsconf.add_allowed_remote_certificate(cert=str(ROOT_CERTS_DIR / "server.cer"))
        tlsconf.set_version(min=c104.TlsVersion.TLS_1_2, max=c104.TlsVersion.TLS_1_3)
        print(f"[TLS Config] Client TLS configuration loaded successfully from: {ROOT_CERTS_DIR}")
        return tlsconf
    except FileNotFoundError as e:
        print(f"[TLS Config] ERROR: Certificate file not found - {e}.")
        return None

# --- CALLBACK FOR DATA RECEPTION ---
def on_point_report(point: c104.Point, previous_info: c104.Information, message: c104.IncomingMessage):
    """Callback function to handle and print incoming data from the server."""
    print(
        f"CLIENT DATA | IOA: {point.io_address:<5} | "
        f"Value: {point.value:<8.2f} | "
        f"Quality: {str(point.quality):<15} | "
        f"Timestamp: {point.recorded_at}"
    )
    return c104.ResponseState.SUCCESS

# --- DYNAMIC POINT CONFIGURATION ---
def configure_points_from_map():
    """Reads the server-generated map and configures local points to monitor."""
    global station, points_configured
    with client_lock:
        if points_configured:
            return

        try:
            map_file_path = path_config.path_cfg.base_path + "IEC_RTU/IEC_point_map.json"
            with open(map_file_path, 'r') as f:
                point_map = json.load(f)
            
            print("\n--- [IEC Client] Point map found. Configuring points for monitoring... ---")
            for ioa_str, info in point_map.items():
                ioa = int(ioa_str)
                if not station.get_point(ioa):
                    point = station.add_point(io_address=ioa, type=c104.Type.M_ME_NC_1)
                    point.on_receive(callable=on_point_report)
                    print(f"  -> Monitoring IOA {ioa} ({info['device_id']} -> {info['parameter']})")
            
            points_configured = True
            print("--- [IEC Client] Point configuration complete. ---")
            
        except FileNotFoundError:
            print(f"--- [IEC Client] WAITING: Point map file not found at {map_file_path}.")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"--- [IEC Client] ERROR: Could not parse point map file. Error: {e}")
            if client and client.is_running: client.stop()

# --- MAIN CLIENT LOGIC ---
def main():
    global client, connection, station

    tls_settings = get_client_tls_config()
    if not tls_settings:
        print("--- [IEC Client] CRITICAL: Could not load TLS settings. Client will not start. ---")
        return

    try:
        client = c104.Client(transport_security=tls_settings)
        connection = client.add_connection(ip="127.0.0.1", port=2404, init=c104.Init.INTERROGATION)
        station = connection.add_station(common_address=3000)
        
        print("\nPress Enter to start the client...")
        input()
        client.start()

        while not connection.is_connected:
            print("--- [IEC Client] Attempting to connect to the server... ---")
            time.sleep(2)
        print("--- [IEC Client] Secure connection established with server. ---")

        while client.is_running:
            if not points_configured:
                configure_points_from_map()
            else:
                print("\n--- [IEC Client] Sending General Interrogation to fetch all point values... ---")
                connection.send_interrogation(station.common_address)
            
            time.sleep(15)

    except KeyboardInterrupt:
        print("\n--- [IEC Client] User interrupted. Stopping client... ---")
    except Exception as e:
        print(f"--- [IEC Client] An unexpected error occurred: {e} ---")
    finally:
        if 'client' in globals() and client and client.is_running:
            client.stop()
        print("--- [IEC Client] Client stopped. ---")

if __name__ == "__main__":
    if 'path_config' not in sys.modules:
        class MockPathConfig:
            def __init__(self): self.base_path = "./"
        path_config.path_cfg = MockPathConfig()

    main()
