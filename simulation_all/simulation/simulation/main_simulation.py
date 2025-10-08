# 

import json
import threading
import time
from datetime import datetime
import requests
from device_emulator import Device


def load_devices(config_path):
    with open(config_path) as f:
        cfg = json.load(f)

    devices = []
    for d in cfg["device_list"]:
        device = Device(
            device_name=d["part_num"],
            port=int(d["modbus_tcp_details"]["port"]),
            slave_id=int(d["modbus_tcp_details"].get("slave_id", 1)),
            params={
                "L1_voltage": 230,
                "L2_voltage": 230,
                "L3_voltage": 230,
                "total_power": int(d.get("rated_power", 3000))
            }
        )
        devices.append(device)
    return devices


def send_batch_to_backend(devices, url):
    while True:
        now = datetime.now()
        local_date = now.strftime("%Y-%m-%d")
        timestamp = int(time.time())

        payload = {
            "timestamp": timestamp
        }

        for idx, dev in enumerate(devices, start=1):
            dev_id = f"dev{idx}"
            key_value = dev.params.get("total_power", 0)  # You can replace "total_power" with other param if needed
            payload[dev_id] = {
                "local_date": local_date,
                "key": key_value
            }

        try:
            requests.post(url, json=[payload], timeout=3)
            print(f"[PUSH] Sent to backend: {payload}")
        except Exception as e:
            print("[ERROR] Sending to backend failed:", e)

        time.sleep(5)  # Send every 5 seconds


if __name__ == "__main__":
    devices = load_devices("installer_cfg.json")

    # Start each device's server and data simulation loop
    for dev in devices:
        threading.Thread(target=dev.run_server, daemon=True).start()
        threading.Thread(target=dev.run_loop, daemon=True).start()

    # Start backend push loop
    backend_url = "http://192.168.1.39:8080/ui/client/no-auth/timescaledb/save-data"
    threading.Thread(target=send_batch_to_backend, args=(devices, backend_url), daemon=True).start()

    # Keep main thread alive
    while True:
        time.sleep(10)
