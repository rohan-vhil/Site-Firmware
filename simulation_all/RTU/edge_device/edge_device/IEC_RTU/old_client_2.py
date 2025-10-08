import c104
import time
import datetime

ROOT = "/home/harsh/repositories/vhil/vhil_ED/edge_device/tests/"

def main():
    # Client, connection and station preparation (no changes here)
    client = c104.Client(tick_rate_ms=1000, command_timeout_ms=1000, transport_security=None)
    print("CL] Client created")

    connection = client.add_connection(ip="127.0.0.1", port=2404, init=c104.Init.ALL)
    station = connection.add_station(common_address=3000)
    
    # We will read the first data point with IOA 3001
    point = station.add_point(io_address=3001, type=c104.Type.M_ME_NC_1)

    # Start the client
    client.start()

    # Wait until the connection to the server is established
    while connection.state != c104.ConnectionState.OPEN:
        print(f"CL] Waiting for connection to {connection.ip}:{connection.port}...")
        time.sleep(1)

    print("CL] Connection established. Starting continuous data polling...")
    print("CL] Press Ctrl+C to exit.")

    # --- KEY CHANGE: CONTINUOUS READ LOOP ---
    try:
        while True:
            # Request the latest data from the server for our point
            if point.read():
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] -> SUCCESS | IOA {point.io_address} Value: {point.value}")
            else:
                print(f"[{timestamp}] -> FAILED to read from IOA {point.io_address}")
            
            # Wait for 5 seconds before the next read
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nCL] Polling stopped by user.")
    finally:
        # Cleanly stop the client
        client.stop()
        print("CL] Client stopped.")


if __name__ == "__main__":
    main()
