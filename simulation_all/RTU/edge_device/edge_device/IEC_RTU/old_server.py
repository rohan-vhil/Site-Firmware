import c104
import time
import path_config
import json
import threading

server = None
vals = {}
server_data_lock = threading.Lock()

def ReaderFunc(device_name, param_name):
    def dataReader(point: c104.Point) -> None:
        try:
            with server_data_lock:
                point.value = vals.get(device_name, {}).get(param_name, 0.0)
        except Exception as e:
            point.value = 0.0
            print(f"IEC ReaderFunc Error: {e}")
    return dataReader

def startIECServer():
    global server
    server = c104.Server()

    with open(path_config.path_cfg.base_path + "IEC_RTU/RTU_addr_config.json") as rtu_file:
        rtu_json = json.load(rtu_file)

    station = server.add_station(common_address=3000)
    
    io_address_counter = rtu_json["analog_signals"]["start_address"]

    for device in rtu_json["analog_signals"]["devices"]:
        device_name = device["device_name"]
        for data_object in device["data_objects"]:
            param_name = data_object["name"]
            
            func_name = f"ReaderFunc_{device_name}_{param_name}"
            globals()[func_name] = ReaderFunc(device_name, param_name)
            
            point_type_str = data_object["type"]
            point = station.add_point(
                io_address=io_address_counter, 
                type=getattr(c104.Type, point_type_str)
            )
            point.on_before_read(callable=globals()[func_name])
            
            io_address_counter += 1
            
    server.start()
    print("IEC 104 Server Component Started.")

def runServer(data_handler_object):
    global vals

    FIRMWARE_ID_TO_IEC_NAME_MAP = {
        '0': 'inverter1',
        '1': 'inverter2',
        '2': 'load_meter',
        '3': 'grid_meter'
    }

    while True:
        if hasattr(data_handler_object, 'avg_data'):
            latest_firmware_data = data_handler_object.avg_data
            transformed_data = {}

            for device_id_str, params in latest_firmware_data.items():
                iec_device_name = FIRMWARE_ID_TO_IEC_NAME_MAP.get(device_id_str)
                if iec_device_name:
                    transformed_data[iec_device_name] = {}
                    if "total_power" in params:
                        transformed_data[iec_device_name]['power'] = params["total_power"]
                    if "L1_voltage" in params:
                        transformed_data[iec_device_name]['voltage'] = params["L1_voltage"]
                    if "acfreq" in params:
                        transformed_data[iec_device_name]['frequency'] = params["acfreq"]
                    if "Q" in params:
                        transformed_data[iec_device_name]['reactive_power'] = params["Q"]

            with server_data_lock:
                vals = transformed_data
                
        time.sleep(1)
