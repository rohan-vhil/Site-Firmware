from iec104 import Client

def on_asdu(asdu):
    print("Received ASDU:", asdu)

client = Client()
client.connect("192.168.1.100", 2404)
client.set_asdu_callback(on_asdu)

client.send_interrogation()
client.run()
