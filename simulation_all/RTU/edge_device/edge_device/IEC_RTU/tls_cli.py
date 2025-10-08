import c104
import time
import json
from pathlib import Path
import sys

# Assuming path_config is in a location accessible via sys.path
sys.path.insert(0,"../")
import path_config

# --- GLOBAL VARIABLES ---
client: c104.Client
connection: c104.Connection
station: c104.Station
points_configured = False
client_lock = threading.Lock()

# --- TLS SECURITY CONFIGURATION ---
def get_client_tls_config():
    """
    Configures and returns the TLS settings for the IEC 104 client.
    This function is self-contained and loads all necessary certificates.
    """
    # Define the root directory, assuming a 'certs' folder is alongside this script
    ROOT = Path(__file__).absolute().parent
    
    try:
        tlsconf = c104.TransportSecurity(validate=False, only_known=False)
        
        # 1. Set the client's own certificate and private key for authentication.
        tlsconf.set_certificate(
            cert=str(ROOT / "certs/client1.cer"), 
            key=str(ROOT / "certs/client1-key.pem")
        )
        
        # 2. Set the Certificate Authority (CA) to verify the server's certificate.
        tlsconf.set_ca_certificate(cert=str(ROOT / "certs/root.cer"))
        
        # 3. Specify the server certificate that is trusted.
        tlsconf.add_allowed_remote_certificate(cert=str(ROOT / "certs/server.cer"))

        # 4. Enforce a minimum TLS version for security.
        tlsconf.set_version(min=c104.TlsVersion.TLS_1_2, max=c104.TlsVersion.TLS_1_3)
        
        print("[TLS Config] Client TLS configuration loaded successfully.")
        return tlsconf
        
    except FileNotFoundError as e:
        print(f"[TLS Config] ERROR: Certificate file not found - {e}. Please ensure the 'certs' folder is correct.")
        return None
    except Exception as e:
        print(f"[TLS Config] ERROR: An unexpected error occurred while creating client TLS config: {e}")
        return None

# --- CALLBACK FOR DATA RECEPTION ---
def on_point_report(point: c104.Point, message: c104.IncomingMessage):
    """Callback function to handle and print incoming data from the server."""
    print(
        f"CLIENT DATA | IOA: {point.io_address}, "
        f"Value: {point.value:.2f}, "
        f"Timestamp: {point.recorded_at}, "
        f"Quality: {point.quality}"
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
                point = station.add_point(io_address=ioa, type=c104.Type.M_ME_NC_1)
                point.on_receive(callable=on_point_report)
                print(f"  -> Monitoring IOA {ioa} ({info['device_id']} -> {info['parameter']})")
            
            points_configured = True
            print("--- [IEC Client] Point configuration complete. ---")
            
        except FileNotFoundError:
            print(f"--- [IEC Client] WAITING: Point map file not found at {map_file_path}. Waiting for server to create it.")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"--- [IEC Client] ERROR: Could not read or parse point map file. Error: {e}")
            # Stop the client if the map is corrupt to avoid issues
            if client.is_running:
                client.stop()


# --- MAIN CLIENT LOGIC ---
def main():
    global client, connection, station

    # 1. Load TLS Settings
    tls_settings = get_client_tls_config()
    if not tls_settings:
        print("--- [IEC Client] CRITICAL: Could not load TLS settings. Client will not start. ---")
        return

    try:
        # 2. Initialize Client
        client = c104.Client(transport_security=tls_settings)
        connection = client.add_connection(ip="127.0.0.1", port=2404)
        station = connection.add_station(common_address=3000)
        
        print("\nPress Enter to start the client...")
        input()
        client.start()

        # 3. Wait for Connection
        while not connection.is_connected:
            print("--- [IEC Client] Attempting to connect to the server... ---")
            time.sleep(2)
        print("--- [IEC Client] Secure connection established with server. ---")

        # 4. Main Loop
        while client.is_running:
            if not points_configured:
                # Attempt to configure points until successful
                configure_points_from_map()
            else:
                # Once configured, perform a general interrogation periodically
                print("\n--- [IEC Client] Sending General Interrogation to fetch all point values... ---")
                connection.send_interrogation(station.common_address)
            
            time.sleep(15) # Poll every 15 seconds

    except KeyboardInterrupt:
        print("\n--- [IEC Client] Stopping client... ---")
    except Exception as e:
        print(f"--- [IEC Client] An unexpected error occurred: {e} ---")
    finally:
        if 'client' in globals() and client.is_running:
            client.stop()
        print("--- [IEC Client] Client stopped. ---")

if __name__ == "__main__":
    # Mock path_config for standalone testing if needed
    if 'path_config' not in sys.modules:
        class MockPathConfig:
            def __init__(self):
                self.base_path = "./"
        path_config.path_cfg = MockPathConfig()

    main()
