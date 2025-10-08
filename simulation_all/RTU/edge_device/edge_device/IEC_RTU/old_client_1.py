import c104
import random
import time
ROOT = "/home/edge_device/RTU/edge_device/edge_device/tests/"
import datetime


def con_on_unexpected_message(connection: c104.Connection, message: c104.IncomingMessage, cause: c104.Umc) -> None:
    if cause == c104.Umc.MISMATCHED_TYPE_ID :
        station = connection.get_station(message.common_address)
        if station:
            point = station.get_point(message.io_address)
            if point:
                print("CL] <-in-- CONFLICT | SERVER CA {0} reports IOA {1} type as {2}, but is already registered as {3}".format(message.common_address, message.io_address, message.type, point.type))
                return
    print("CL] <-in-- REJECTED | {1} from SERVER CA {0}".format(message.common_address, cause))

def recieveSet(point : c104.Point,previous_info:c104.Information,message: c104.IncomingMessage,)->c104.ResponseState:
    print("recieved in auto transmit: ",point.value)
    return c104.ResponseState.SUCCESS


def main():
    # client, connection and station preparation
    tlsconf = c104.TransportSecurity(validate=True, only_known=False)
    tlsconf.set_certificate(cert=str(ROOT + "certs/client1.crt"), key=str(ROOT + "certs/client1.key"))

    tlsconf.set_ca_certificate(cert=str(ROOT + "certs/ca.crt"))

    tlsconf.add_allowed_remote_certificate(cert=str(ROOT + "certs/server1.crt"))
    tlsconf.set_version(min=c104.TlsVersion.TLS_1_2, max=c104.TlsVersion.TLS_1_3)
    #tlsconf.set_renegotiation_time(interval=datetime.timedelta(minutes=5))
    #tlsconf.set_resumption_interval(interval=datetime.timedelta(hours=1))
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

    client = c104.Client(tick_rate_ms=1000,command_timeout_ms=1000,transport_security=None)

    print("client created")
    connection = client.add_connection(ip="127.0.0.1", port=2404, init=c104.Init.ALL)
    #connection.on_unexpected_message(callable=con_on_unexpected_message)
    station = connection.add_station(common_address=3000)
    # monitoring point preparation
    point = station.add_point(io_address=3001, type=c104.Type.M_ME_NC_1)
    print(point.value)

    # command point preparation
    #command = station.add_point(io_address=12, type=c104.Type.C_RC_TA_1)
    #command.value = c104.Step.HIGHER

    # start
    client.start()
    #point.on_receive(callable=recieveSet)
    #while(1):
    #    print(connection.state)
    #    time.sleep(1)
    while connection.state != c104.ConnectionState.OPEN:
        print("Waiting for connection to {0}:{1}".format(connection.ip, connection.port))
        time.sleep(1)

    print(f"-> AFTER INIT {point.value}")

    print("read")
    print("read")
    print("read")
    if point.read():
        print(f"-> SUCCESS {point.value}")
    else:
        print("-> FAILURE")

    #time.sleep(3)
    """
    print("transmit")
    print("transmit")
    print("transmit")
    if command.transmit(cause=c104.Cot.ACTIVATION):
        print("-> SUCCESS")
    else:
        print("-> FAILURE")

    time.sleep(3)

    print("exit")
    print("exit")
    print("exit")
    """


if __name__ == "__main__":
    # c104.set_debug_mode(c104.Debug.Client|c104.Debug.Connection|c104.Debug.Point|c104.Debug.Callback)
    main()
