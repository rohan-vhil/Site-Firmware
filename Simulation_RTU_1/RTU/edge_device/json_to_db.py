import json
import psycopg2
from psycopg2.extras import Json

DB_CONFIG = {
    'dbname': 'raspberrypi',
    'user': 'harshal',
    'password': 'harshal',
    'host': 'localhost',
    'port': 5432,
}

JSON_FILE_PATH = 'mappings.json'

def insert_devices_into_db(json_file_path, db_config):
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    for device_model_no, modbus_addresses in data.items():
        device_modbus_addresses = json.dumps(modbus_addresses)

        cursor.execute("""
            UPDATE masterdevices
            SET device_modbus_addresses = %s
            WHERE device_model_no = %s;
        """, (
            device_modbus_addresses,
            device_model_no
        ))

    conn.commit()
    cursor.close()
    conn.close()
    print("Insertions complete.")

if __name__ == '__main__':
    insert_devices_into_db(JSON_FILE_PATH, DB_CONFIG)
