from RaspberryPI.models.rpi_models import MasterDevices
from sqlalchemy import tuple_
import json
import os


def query_master_devices(devices, db_psql):
    brand_model_pairs = [(device["device_brand"], device["part_num"]) for device in devices]
    if brand_model_pairs:
        masterdevices = db_psql.query(
            MasterDevices.device_brand,
            MasterDevices.device_model_no,
            MasterDevices.device_modbus_addresses,
            MasterDevices.device_fault_codes
        ).filter(
            tuple_(MasterDevices.device_brand, MasterDevices.device_model_no).in_(brand_model_pairs)
        ).all()
    else:
        masterdevices = []
    return masterdevices

def update_installer_cfg(devices, file_path):
    try:
        with open(file_path, 'r') as file:
            installer_cfg = json.load(file)

        existing_devices = installer_cfg.get('device_list', [])
        updated_device_list = existing_devices + devices

        installer_cfg['device_list'] = updated_device_list
        installer_cfg['number_of_devices'] = len(updated_device_list)

        with open(file_path, 'w') as file:
            json.dump(installer_cfg, file, indent=4)

        print(f"Successfully updated {file_path} with {len(devices)} new devices. Total devices: {len(updated_device_list)}")

    except Exception as e:
        print(f"An error occurred: {e}")

    
def save_as_json(new_data, file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, 'r') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                print("Warning: Existing file is not valid JSON. Overwriting.")
                existing_data = {}
    else:
        existing_data = {}

    if not isinstance(existing_data, dict):
        print("Warning: Existing data is not a JSON object. Overwriting with new data.")
        merged_data = new_data
    else:
        merged_data = {**existing_data, **new_data}

    with open(file_path, 'w') as f:
        json.dump(merged_data, f, indent=4)
    
    print(f"Data successfully appended to {file_path}")

def save_as_list(new_data, file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, 'r') as f:
            try:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    print("Warning: Existing data is not a list. Overwriting with new list.")
                    existing_data = []
            except json.JSONDecodeError:
                print("Warning: Existing file is not valid JSON. Overwriting with new list.")
                existing_data = []
    else:
        existing_data = []

    if isinstance(new_data, list):
        existing_data.extend(new_data)
    else:
        existing_data.append(new_data)

    with open(file_path, 'w') as f:
        json.dump(existing_data, f, indent=4)

    print(f"Data successfully saved to {file_path}")