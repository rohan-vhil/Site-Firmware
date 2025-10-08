# simple_client.py
# Description: Connects to the local IEC-104 server to verify it's working.
# This script is separate from the new data publishing feature.

import c104
import time
import datetime
import json
import os

MAP_FILE_PATH = "IEC_point_map.json" 

def main():
    print(f"CL] Waiting for the map file '{MAP_FILE_PATH}'...")
    while not os.path.exists(MAP_FILE_PATH):
        time.sleep(1)
    
    with open(MAP_FILE_PATH, 'r') as f:
        point_map = json.load(f)
    print("CL] Map file found. Configuring client...")

    client = c104.Client(tick_rate_ms=1000, command_timeout_ms=5000)
    connection = client.add_connection(ip="127.0.0.1", port=2404, init=c104.Init.ALL)
    station = connection.add_station(common_address=3000)
    
    points_to_poll = []
    for io_addr_str, info in point_map.items():
        io_address = int(io_addr_str)
        point = station.add_point(io_address=io_address, type=c104.Type.M_ME_NC_1)
        points_to_poll.append((point, info))
        print(f"  -> Client configured for IOA {io_address} ({info['device_id']} -> {info['parameter']})")

    client.start()

    while connection.state != c104.ConnectionState.OPEN:
        print(f"CL] Waiting for connection to {connection.ip}:{connection.port}...")
        time.sleep(1)

    print("\nCL] Connection established. Starting continuous data polling...")
    print("CL] Press Ctrl+C to exit.")

    try:
        while True:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n--- Polling data at {timestamp} ---")
            
            for point, info in points_to_poll:
                if point.read():
                    print(f"  -> SUCCESS | {info['device_id']:<40} | {info['parameter']:<15} | Value: {point.value}")
                else:
                    print(f"  -> FAILED  | {info['device_id']:<40} | {info['parameter']:<15} | No response")
            
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nCL] Polling stopped by user.")
    finally:
        client.stop()
        print("CL] Client stopped.")

if __name__ == "__main__":
    main()
