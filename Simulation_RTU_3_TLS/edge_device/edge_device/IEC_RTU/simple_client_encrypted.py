'''import base64
import json
from flask import Flask, request, jsonify

# --- Import cryptography modules ---
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding as rsa_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding

# --- CONFIGURATION ---
SLDC_PRIVATE_KEY_PATH = "sldc_private.pem" # The receiver uses the private key
sldc_private_key = None

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Decryption Logic ---
@app.route('/publish', methods=['POST'])
def handle_publish():
    global sldc_private_key
    if not sldc_private_key:
        return jsonify({"error": "Server private key not loaded"}), 500

    try:
        # 1. Get the incoming encrypted payload
        payload = request.json
        encrypted_key_b64 = payload['encrypted_key']
        iv_b64 = payload['iv']
        encrypted_data_b64 = payload['encrypted_data']
        
        print("\n--- [Receiver] Received new encrypted payload ---")
        # print(f"  -> Encrypted Key (b64): {encrypted_key_b64[:30]}...")
        # print(f"  -> IV (b64): {iv_b64}")
        # print(f"  -> Encrypted Data (b64): {encrypted_data_b64[:30]}...")

        # 2. Base64 decode all parts back to binary
        encrypted_session_key = base64.b64decode(encrypted_key_b64)
        iv = base64.b64decode(iv_b64)
        encrypted_data = base64.b64decode(encrypted_data_b64)
        
        # 3. Decrypt the AES session key using the SLDC's private RSA key
        session_key = sldc_private_key.decrypt(
            encrypted_session_key,
            rsa_padding.OAEP(
                mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # 4. Decrypt the data using the now-revealed session key
        cipher = Cipher(algorithms.AES(session_key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # 5. Unpad the decrypted data
        unpadder = sym_padding.PKCS7(128).unpadder()
        original_data_bytes = unpadder.update(padded_data) + unpadder.finalize()

        # 6. Decode the bytes back to a JSON object
        original_data_dict = json.loads(original_data_bytes.decode('utf-8'))
        
        print("\n--- [Receiver] DECRYPTION SUCCESSFUL ---")
        print(json.dumps(original_data_dict, indent=2))
        print("----------------------------------------\n")

        return jsonify({"status": "success", "message": "Data received and decrypted."}), 200

    except Exception as e:
        print(f"\n--- [Receiver] DECRYPTION FAILED: {e} ---\n")
        return jsonify({"status": "error", "message": str(e)}), 400

# --- Main execution ---
if __name__ == '__main__':
    try:
        with open(SLDC_PRIVATE_KEY_PATH, "rb") as key_file:
            sldc_private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None # Assuming the key is not password-protected
            )
        print(f"--- [Receiver] SLDC private key loaded from '{SLDC_PRIVATE_KEY_PATH}' ---")
    except FileNotFoundError:
        print(f"--- [Receiver] FATAL ERROR: SLDC private key not found at '{SLDC_PRIVATE_KEY_PATH}'. Cannot decrypt data. ---")
        exit()

    app.run(host='127.0.0.1', port=5000)
'''

import base64
import json
from flask import Flask, request, jsonify
import os

# --- Import cryptography modules ---
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding as rsa_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding

# --- CONFIGURATION ---
# --- Get the absolute path to the directory where this script resides ---
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

# --- Path to the SLDC's private key, now relative to this script's location ---
SLDC_PRIVATE_KEY_PATH = os.path.join(SCRIPT_DIR, "sldc_private.pem")
sldc_private_key = None

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Decryption Logic ---
@app.route('/publish', methods=['POST'])
def handle_publish():
    global sldc_private_key
    if not sldc_private_key:
        return jsonify({"error": "Server private key not loaded"}), 500

    try:
        # 1. Get the incoming encrypted payload
        payload = request.json
        encrypted_key_b64 = payload['encrypted_key']
        iv_b64 = payload['iv']
        encrypted_data_b64 = payload['encrypted_data']
        
        print("\n--- [Receiver] Received new encrypted payload ---")

        # 2. Base64 decode all parts back to binary
        encrypted_session_key = base64.b64decode(encrypted_key_b64)
        iv = base64.b64decode(iv_b64)
        encrypted_data = base64.b64decode(encrypted_data_b64)
        
        # 3. Decrypt the AES session key using the SLDC's private RSA key
        session_key = sldc_private_key.decrypt(
            encrypted_session_key,
            rsa_padding.OAEP(
                mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # 4. Decrypt the data using the now-revealed session key
        cipher = Cipher(algorithms.AES(session_key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # 5. Unpad the decrypted data
        unpadder = sym_padding.PKCS7(128).unpadder()
        original_data_bytes = unpadder.update(padded_data) + unpadder.finalize()

        # 6. Decode the bytes back to a JSON object
        original_data_dict = json.loads(original_data_bytes.decode('utf-8'))
        
        print("\n--- [Receiver] DECRYPTION SUCCESSFUL ---")
        print(json.dumps(original_data_dict, indent=2))
        print("----------------------------------------\n")

        return jsonify({"status": "success", "message": "Data received and decrypted."}), 200

    except Exception as e:
        print(f"\n--- [Receiver] DECRYPTION FAILED: {e} ---\n")
        return jsonify({"status": "error", "message": str(e)}), 400

# --- Main execution ---
if __name__ == '__main__':
    try:
        with open(SLDC_PRIVATE_KEY_PATH, "rb") as key_file:
            sldc_private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )
        print(f"--- [Receiver] SLDC private key loaded from '{SLDC_PRIVATE_KEY_PATH}' ---")
    except FileNotFoundError:
        print(f"--- [Receiver] FATAL ERROR: SLDC private key not found at '{SLDC_PRIVATE_KEY_PATH}'. Cannot decrypt data. ---")
        exit()

    app.run(host='127.0.0.1', port=5000)
