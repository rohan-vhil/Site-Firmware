# dummy_receiver.py
# Description: A simple Flask web server to receive and display JSON data from the simple_server.
# Installation: You need to install Flask -> pip install Flask

from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# A global variable to store the last received data payload
last_received_data = {
    "status": "No data received yet. Waiting for the first POST request to /publish..."
}

@app.route('/publish', methods=['POST'])
def receive_data():
    """
    This endpoint listens for POST requests from the simple_server.
    """
    global last_received_data
    try:
        data = request.get_json()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"--- [ {timestamp} ] Data Received from IEC Server ---")
        print(json.dumps(data, indent=4))
        print("---------------------------------------------------\n")
        
        last_received_data = {
            "last_updated": timestamp,
            "source": "IEC_104_Server",
            "payload": data
        }
        
        return jsonify({"status": "success", "message": "Data received"}), 200
    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/latest', methods=['GET'])
def get_latest_data_api():
    """
    This endpoint provides the latest data as a JSON response for the viewer script.
    """
    return jsonify(last_received_data)

if __name__ == '__main__':
    print("Dummy Receiver Server is running.")
    print(" - The simple_server will POST data to: http://127.0.0.1:5000/publish")
    print(" - The viewer script will poll: http://127.0.0.1:5000/api/latest")
    app.run(host='0.0.0.0', port=5000, debug=False)
