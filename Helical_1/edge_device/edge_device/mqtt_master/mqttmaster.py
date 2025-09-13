from control import control_base as ctrl
import paho.mqtt.client as mqtt
import json
from socket import gaierror
import time
import logging


class mqttConection:
    ip:str
    topic: str
    mqtt_client:mqtt.Client
    connect_flag: bool = False

    def __init__(self, ip) -> None:
        self.ip = ip
        try:
            self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except Exception as e:
            self.mqtt_client = mqtt.Client()
        pass
        

    def mqttConnect(self):
        try:
            self.mqtt_client.connect(self.ip, port=1883, keepalive=60)
        except gaierror as e:
            time.sleep(5)
            return -1
        self.mqtt_client.loop_start()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        #self.mqtt_client.on_publish = on_mqtt_send
    
    def mqttSubscribe(self, topic):
        self.topic = topic
        print("subscribe to ",topic)
        self.mqtt_client.subscribe(topic=topic)
    
    def mqttPublish(self,topic,message):
        #message_json = json.loads(message)
        logging.warning(str(message)+str(topic))
        print(self.mqtt_client.publish(topic="action/ack/" + str(ctrl.controller_id), payload=message))






    def on_mqtt_message(self,client,userdata,message):
        logging.warning("mqtt message recieved :" + str(message.payload.decode('utf-8')))
        msg_str=message.payload.decode('utf-8')
        msg_json = json.loads(msg_str)
        #self.mqttPublish(self.topic , msg_str)
        if("schedule" in msg_json):
            with open('control/ctrl_cfg/ctrl_cfg.json','w+') as ctrl_cfg:
                json.dump(msg_json,ctrl_cfg)
                ctrl.setModeSrc("schedule")

        else:
            ctrl.setModeSrc("direct")
            ctrl.setParameter(msg_json)
        self.mqttPublish(self.topic , msg_str)
    # if('ref' in msg_json):
    #     ref = msg_json['ref']
    def on_mqtt_connect(self,s,client, userdata,rc,prop=0):
        logging.info('MQTT client connected')
        self.connect_flag = True
    # else:
    #     ref = 0
    # mode_str=msg_json['mode']
    # ctrl.updateOperatingMode(mode_str,ref)
    
    
    # if "mode" in msg_json.keys():
    #     pass
    # elif "power" in msg_json.keys():
    #     pass
    # elif "current" in msg_json.keys():
    #     pass
    # elif "device_state" in msg_json.keys():
    #     pass
    




mqtt_connection : mqttConection
