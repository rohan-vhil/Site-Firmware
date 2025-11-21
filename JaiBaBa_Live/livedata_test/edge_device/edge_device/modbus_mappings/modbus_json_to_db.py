import psycopg2
import json


conn = psycopg2.connect(
    host="localhost",user = 'postgres',password = 'postgres',database = 'raspberrypi')

querry = ""

json_file = json.load(open('mappings.json'))
error_file = json.load(open('error_codes.json'))
#print(json_file)


device_names = ["UMG104"]
for device_name in json_file:
    
        
    device = json_file[device_name]
    try:
        error = error_file[device_name]
    except:
        error = {}
    brand = device["block1"]["brand"]
    type = device["block1"]["type"]

    specs = {"spec1":"value1","spec2":"value2"}
    querry = "INSERT INTO masterdevices (device_type, device_brand, device_model_no, device_specifications,device_modbus_addresses, device_fault_codes) VALUES "
    values = f"('{type}','{brand}','{device_name}','{json.dumps(specs)}','{json.dumps(device)}','{json.dumps(error)}');"
    querry += values
    print(querry) 
    try:
        cursor = conn.cursor()
        cursor.execute(querry)
        conn.commit()
    except Exception as e:
        print(e)
    print("insert complete==========")
