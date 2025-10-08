'''import c104
import time
import sys
import json
import threading
import requests
import base64
import os

# --- NEW: Import cryptography modules ---
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding as rsa_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding

sys.path.insert(0,"../")
import path_config

# --- CONFIGURATION ---
DUMMY_PUBLISH_URL = "http://127.0.0.1:5000/publish"
PUBLISH_INTERVAL_SECONDS = 10
# --- NEW: Path to the SLDC's public key ---
SLDC_PUBLIC_KEY_PATH = "sldc_public.pem" 

# --- GLOBAL VARIABLES ---
server: c104.Server
station: c104.Station
vals: dict = {}
points_created = False
# --- NEW: Global variable for the loaded public key ---
sldc_public_key = None

# --- HELPER FUNCTION (Unchanged) ---
def ReaderFunc(device_id, param_name):
    # ... (This function is exactly the same as your original)
    def dataReader(point: c104.Point) -> None:
        try:
            point.value = float(vals[str(device_id)][param_name])
        except (KeyError, TypeError):
            pass
    return dataReader

# --- DYNAMIC POINT CREATION (Unchanged) ---
def create_dynamic_points(data):
    # ... (This function is exactly the same as your original)
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


# --- NEW: ENCRYPTION HELPER FUNCTION ---
def encrypt_payload(data_dict: dict, public_key) -> dict:
    """
    Encrypts a data dictionary using the hybrid encryption scheme.
    Returns a dictionary containing the encrypted payload.
    """
    # 1. Serialize the data to a JSON string, then to bytes
    data_bytes = json.dumps(data_dict).encode('utf-8')

    # 2. Generate a one-time AES session key and an IV
    session_key = os.urandom(32)  # AES-256 key
    iv = os.urandom(16)           # AES block size for CBC is 16 bytes

    # 3. Encrypt the data with the AES session key
    # Pad the data to be a multiple of the block size
    padder = sym_padding.PKCS7(128).padder()
    padded_data = padder.update(data_bytes) + padder.finalize()
    
    # Create cipher and encrypt
    cipher = Cipher(algorithms.AES(session_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # 4. Encrypt the AES session key with the SLDC's public RSA key
    encrypted_session_key = public_key.encrypt(
        session_key,
        rsa_padding.OAEP(
            mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # 5. Base64 encode all binary parts for safe JSON transport
    # The receiver will also need the IV to decrypt the data
    final_payload = {
        "encrypted_key": base64.b64encode(encrypted_session_key).decode('utf-8'),
        "iv": base64.b64encode(iv).decode('utf-8'),
        "encrypted_data": base64.b64encode(encrypted_data).decode('utf-8')
    }
    
    return final_payload

# --- UPDATED: DATA PUBLISHING THREAD ---
def publish_data_periodically():
    """This function runs in a background thread and sends ENCRYPTED data."""
    while True:
        time.sleep(PUBLISH_INTERVAL_SECONDS)
        
        # Check if there is data and the public key has been loaded
        if vals and sldc_public_key: 
            try:
                print(f"\n--- [IEC Server] Encrypting data for publishing...")
                # Make a thread-safe copy of the data
                data_to_send = vals.copy()
                
                # --- NEW: Encrypt the data before sending ---
                encrypted_payload = encrypt_payload(data_to_send, sldc_public_key)
                
                response = requests.post(DUMMY_PUBLISH_URL, json=encrypted_payload, timeout=5)
                
                if response.status_code == 200:
                    print(f"--- [IEC Server] Successfully published ENCRYPTED data to {DUMMY_PUBLISH_URL} ---")
                else:
                    print(f"--- [IEC Server] WARN: Failed to publish encrypted data. Status: {response.status_code} ---")
            except requests.exceptions.RequestException as e:
                print(f"--- [IEC Server] ERROR: Could not connect to receiver at {DUMMY_PUBLISH_URL} ---")
            except Exception as e:
                print(f"--- [IEC Server] ERROR: An unexpected error occurred during publishing: {e} ---")

# --- SERVER INITIALIZATION & RUN LOOP (with key loading) ---
def startIECServer():
    global server, station, sldc_public_key
    
    # --- NEW: Load the SLDC public key on startup ---
    try:
        with open(SLDC_PUBLIC_KEY_PATH, "rb") as key_file:
            sldc_public_key = serialization.load_pem_public_key(key_file.read())
        print(f"--- [IEC Server] Successfully loaded SLDC public key from {SLDC_PUBLIC_KEY_PATH} ---")
    except FileNotFoundError:
        print(f"--- [IEC Server] FATAL ERROR: SLDC public key not found at '{SLDC_PUBLIC_KEY_PATH}'. Cannot send encrypted data. ---")
        return # Stop initialization if key is not found
        
    server = c104.Server()
    station = server.add_station(common_address=3000)
    server.start()
    
    publisher_thread = threading.Thread(target=publish_data_periodically, daemon=True)
    publisher_thread.start()
    
    print("--- [IEC Server] Started. IEC-104 service is running. ---")
    print(f"--- [IEC Server] Now also publishing ENCRYPTED data every {PUBLISH_INTERVAL_SECONDS}s to {DUMMY_PUBLISH_URL} ---")

def runServer(data_handler_object):
    # ... (This function is exactly the same as your original)
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
'''

import c104
import time
import sys
import json
import threading
import requests
import base64
import os

# --- Import cryptography modules ---
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding as rsa_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding

# This sys.path insert might need adjustment based on your project structure
sys.path.insert(0,"../")
import path_config

# --- CONFIGURATION ---
#DUMMY_PUBLISH_URL = "http://127.0.0.1:5000/publish"
PUBLISH_URL = "https://app.enercog.com/api/no-auth/tls-test" # <-- Changed
DUMMY_PUBLISH_URL = PUBLISH_URL 
PUBLISH_INTERVAL_SECONDS = 10

# --- Get the absolute path to the directory where this script resides ---
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

# --- Path to the SLDC's public key, now relative to this script's location ---
SLDC_PUBLIC_KEY_PATH = os.path.join(SCRIPT_DIR, "sldc_public.pem")

# --- GLOBAL VARIABLES ---
server: c104.Server
station: c104.Station
vals: dict = {}
points_created = False
sldc_public_key = None

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
    # Adjust this path as needed for your project structure
    map_file_path = os.path.join(SCRIPT_DIR, "IEC_point_map.json")
    with open(map_file_path, 'w') as f:
        json.dump(point_map, f, indent=4)
    print(f"--- Dynamic point creation complete. Map saved to {map_file_path} ---\n")

# --- ENCRYPTION HELPER FUNCTION ---
def encrypt_payload(data_dict: dict, public_key) -> dict:
    data_bytes = json.dumps(data_dict).encode('utf-8')
    session_key = os.urandom(32)
    iv = os.urandom(16)
    padder = sym_padding.PKCS7(128).padder()
    padded_data = padder.update(data_bytes) + padder.finalize()
    cipher = Cipher(algorithms.AES(session_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    encrypted_session_key = public_key.encrypt(
        session_key,
        rsa_padding.OAEP(
            mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    final_payload = {
        "encrypted_key": base64.b64encode(encrypted_session_key).decode('utf-8'),
        "iv": base64.b64encode(iv).decode('utf-8'),
        "encrypted_data": base64.b64encode(encrypted_data).decode('utf-8')
    }
    return final_payload

# --- DATA PUBLISHING THREAD ---
def publish_data_periodically():
    while True:
        time.sleep(PUBLISH_INTERVAL_SECONDS)
        if vals and sldc_public_key:
            try:
                print(f"\n--- [IEC Server] Encrypting data for publishing...")
                data_to_send = vals.copy()
                encrypted_payload = encrypt_payload(data_to_send, sldc_public_key)
                response = requests.post(DUMMY_PUBLISH_URL, json=encrypted_payload, timeout=5)
                if response.status_code == 200:
                    print(f"--- [IEC Server] Successfully published ENCRYPTED data to {DUMMY_PUBLISH_URL} ---")
                    # Print the response body from the server!
                    print(f"--- [IEC Server] Response from server: {response.text} ---")
                else:
                    print(f"--- [IEC Server] WARN: Failed to publish encrypted data. Status: {response.status_code} ---")
                    # It's helpful to print the error response here too
                    print(f"--- [IEC Server] Error Response: {response.text} ---")
            except requests.exceptions.RequestException:
                print(f"--- [IEC Server] ERROR: Could not connect to receiver at {DUMMY_PUBLISH_URL} ---")
            except Exception as e:
                print(f"--- [IEC Server] ERROR: An unexpected error occurred during publishing: {e} ---")

# --- SERVER INITIALIZATION & RUN LOOP ---
def startIECServer():
    global server, station, sldc_public_key
    try:
        with open(SLDC_PUBLIC_KEY_PATH, "rb") as key_file:
            sldc_public_key = serialization.load_pem_public_key(key_file.read())
        print(f"--- [IEC Server] Successfully loaded SLDC public key from {SLDC_PUBLIC_KEY_PATH} ---")
    except FileNotFoundError:
        print(f"--- [IEC Server] FATAL ERROR: SLDC public key not found at '{SLDC_PUBLIC_KEY_PATH}'. Cannot send encrypted data. ---")
        return False
        
    server = c104.Server()
    station = server.add_station(common_address=3000)
    server.start()
    
    publisher_thread = threading.Thread(target=publish_data_periodically, daemon=True)
    publisher_thread.start()
    
    print("--- [IEC Server] Started. IEC-104 service is running. ---")
    print(f"--- [IEC Server] Now also publishing ENCRYPTED data every {PUBLISH_INTERVAL_SECONDS}s to {DUMMY_PUBLISH_URL} ---")
    return True

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
