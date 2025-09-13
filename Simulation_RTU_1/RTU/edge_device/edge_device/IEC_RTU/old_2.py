import c104
import random
import time
import sys
sys.path.insert(0,"../")
import path_config
import json
import inspect

i=0.0
ROOT = "/home/edge_device/RTU/edge_device/edge_device/tests/"

def on_step_command(point: c104.Point, previous_info: c104.Information, message: c104.IncomingMessage) -> c104.ResponseState:
    """ handle incoming regulating step command
    """
    print("{0} STEP COMMAND on IOA: {1}, message: {2}, previous: {3}, current: {4}".format(point.type, point.io_address, message, previous_info, point.info))

    if point.value == c104.Step.LOWER:
        # do something
        return c104.ResponseState.SUCCESS

    if point.value == c104.Step.HIGHER:
        # do something
        return c104.ResponseState.SUCCESS

    return c104.ResponseState.FAILURE


def before_auto_transmit(point: c104.Point) -> None:
    """ update point value before transmission
    """
    point.value = random.random() * 100
    print("{0} BEFORE AUTOMATIC REPORT on IOA: {1} VALUE: {2}".format(point.type, point.io_address, point.value))


def before_read(point: c104.Point) -> None:
    """ update point value before transmission
    """
    global i

    point.value = vals["1"]["L1_voltage"]
    
    #point.value = time.time()
    i += 1
    print("{0} BEFORE READ or INTERROGATION on IOA: {1} VALUE: {2}".format(point.type, point.io_address, point.value),time.time())


def read_power(point : c104.Point):
     point.value = vals


def createFunctions():
    i=0
    install_file_path = path_config.path_cfg.base_path + "../submodules/RpiBackend/app/json_files/installer_cfg.json"
    with open(path_config.path_cfg.base_path + "IEC_RTU/RTU_addr_config.json") as rtu_file:
         rtu_json = json.load(rtu_file)
    functions_list = []
    for device in rtu_json["analog_signals"]["devices"]:
        for object in device["data_objects"]:
            print((object.keys()))

            def readFunc(point: c104.Point)->None:
                 point.value = vals["1"]["L1_voltage"]
                 print("named function",inspect.stack()[0][3])

            readFunc.__name__ = "readFunc_" + str(i) + "_" + object["name"]

            functions_list.append(readFunc)

    

        i += 1

    return functions_list

def ReaderFunc(device_id,param_name):
    def dataReader(point : c104.Point)->None:
            try:
                point.value = vals[str(device_id)][param_name]
            except Exception as e:
                 print(e)
            print("called by loop ==========",device_id,param_name,point.io_address)

    return dataReader



         

def main():
    # server and station preparation
    tlsconf = c104.TransportSecurity(validate=True, only_known=False)
    tlsconf.set_certificate(cert=str(ROOT + "certs/server1.crt"), key=str(ROOT + "certs/server1.key"))

    tlsconf.set_ca_certificate(cert=str(ROOT + "certs/ca.crt"))
    tlsconf.add_allowed_remote_certificate(cert=str(ROOT + "certs/client1.crt"))
    tlsconf.set_version(min=c104.TlsVersion.TLS_1_2, max=c104.TlsVersion.TLS_1_3)
    """
    tlsconf.set_ciphers(ciphers=[
    c104.TlsCipher.ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
    c104.TlsCipher.ECDHE_RSA_WITH_AES_128_GCM_SHA256,
    c104.TlsCipher.ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
    c104.TlsCipher.ECDHE_RSA_WITH_AES_256_GCM_SHA384,
    c104.TlsCipher.ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256,
    c104.TlsCipher.ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256,
    c104.TlsCipher.DHE_RSA_WITH_AES_128_GCM_SHA256,
    c104.TlsCipher.DHE_RSA_WITH_AES_256_GCM_SHA384,
    c104.TlsCipher.DHE_RSA_WITH_CHACHA20_POLY1305_SHA256,
    c104.TlsCipher.TLS1_3_AES_128_GCM_SHA256,
    c104.TlsCipher.TLS1_3_AES_256_GCM_SHA384,
    c104.TlsCipher.TLS1_3_CHACHA20_POLY1305_SHA256
    ])
    """
    server = c104.Server(transport_security=tlsconf)

    station = server.add_station(common_address=47)
    
    # monitoring point preparation
    device_id=1
    name = "power"
    func_name = f"ReaderFunc _{device_id}_{name}"
    globals()[func_name] = ReaderFunc(device_id,name)
    point = station.add_point(io_address=11, type=c104.Type.M_ME_NC_1, report_ms=1000)
    point.on_before_auto_transmit(callable=globals()[func_name])
    point.on_before_read(callable=globals()[func_name])
    
    # command point preparation
    command = station.add_point(io_address=12, type=c104.Type.C_RC_TA_1)
    command.on_receive(callable=on_step_command)

    # start
    val = {}
    
    server.start()
    while(1):

            while not server.has_active_connections:
                print("Waiting for connection")
                time.sleep(1)

            time.sleep(1)

            c = 0
            while server.has_open_connections and c<30:
                c += 1
                print("Keep alive until disconnected")
                time.sleep(1)
    server.stop()

def updateValues(val):
    while(1):
        #print("test RTU loop",val)
        time.sleep(1)


server : c104.Server
vals: dict
read_functions_list : list = []

def startIECServer():
    global server
    server = c104.Server()

    #tlsconf = c104.TransportSecurity(validate=True, only_known=False)
    #tlsconf.set_ca_certificate(cert=str(ROOT + "certs/ca.crt"))
    #tlsconf.set_certificate(cert=str(ROOT + "certs/server1.crt"), key=str(ROOT + "certs/server1.key"))
    #tlsconf.add_allowed_remote_certificate(cert=str(ROOT + "certs/client1.crt"))
    server = c104.Server()
    #server = c104.Server()
    with open(path_config.path_cfg.base_path + "IEC_RTU/RTU_addr_config.json") as rtu_file:
         rtu_json = json.load(rtu_file)
    i=0

    station = server.add_station(common_address=3000)  
    i=0
    start_addr =  rtu_json["analog_signals"]["start_address"]
    for device in rtu_json["analog_signals"]["devices"]:
        for object in device["data_objects"]:
            name = object["name"]
            func_name = f"ReaderFunc_{i}_{name}"
            globals()[func_name] = ReaderFunc(i,name)
            print("function starting the server : ",globals()[func_name].__name__)
            point = station.add_point(io_address=start_addr + i, type=getattr(c104.Type,object["type"]), report_ms=1000)
            #point.on_before_auto_transmit(callable=globals()[func_name])
            point.on_before_read(callable=globals()[func_name])

             
             
            i+=1
            
    #print(rtu_json)
    
    #print("=== test_function === ",ReaderFunc_0_total_power(point))


         

    #global read_functions_list
    #read_functions_list = createFunctions()
    #
    
    # monitoring point preparation
    #device_id=1
    #name = "total_power"
    #f#unc_name = f"ReaderFunc _{device_id}_{name}"
   #globals()[func_name] = ReaderFunc(device_id,name)
    #print("function starting the server : ",globals()[func_name])
    #point = station.add_point(io_address=11, type=c104.Type.M_ME_NC_1, report_ms=1000)
    #point.on_before_auto_transmit(callable=globals()[func_name])
    #point.on_before_read(callable=globals()[func_name])

    # monitoring point preparation
    server.start()


def runServer(val):
    global vals
    while(1):
            #print("RTU loop value : ",val)
            vals = val
            time.sleep(1)

            #while not server.has_active_connections:
            #    print("Waiting for connection")
                #time.sleep(1)

            #time.sleep(1)

            #c = 0
            #while server.has_open_connections and c<30:
            #    c += 1
            #    print("Keep alive until disconnected")
            #    time.sleep(1)



if __name__ == "__main__":
    # c104.set_debug_mode(c104.Debug.Server|c104.Debug.Point|c104.Debug.Callback)
    main()
