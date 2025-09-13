import sys
import json
sys.path.insert(0,"../")
base_path = "/usr/local/bin/"
sys.path.insert(0,base_path+'modbus_mappings/')
import enum
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
import time
import logging
from mqtt_master import mqttmaster
import uuid
from control import control_base as ctrl
class error_type(enum.IntEnum) :
    fault= 0
    @classmethod
    def from_param(cls, obj):
        return int(obj) 


class errRegistor:
    batch_fault_code:int=0
    offset_fault_code:int=0
    batch_device_state:int=0
    offset_device_state:int=0
    fault_size:int=0
    err_decode:dict
    fault_code:int=0
    status_code:int=0
    device_state:str
    alert_message:list = []
    mqtt_alarm_list:list = []
    errror_map:dict
    last_alert_message:str
    active_alert_list:list = []
    last_device_state:str = ""
    error_init = False
    def __init__(self,addr_map,part_num) -> None:
        i=0
        #print(addr_map)
        with open('modbus_mappings/error_codes.json') as error_json:
            self.errror_map = json.load(error_json)[part_num]

        #print(self.errror_map)
        for batch in addr_map['map']:
            #print(addr_map['map'][batch]["data"]["active_power"])
            if 'Fault' in addr_map['map'][batch]["data"]:
                self.error_init = True
                self.batch_fault_code = i
                self.offset_fault_code = (addr_map['map'][batch]["data"]['Fault']["offset"])
                self.fault_size = (addr_map['map'][batch]["data"]["Fault"]["size"])
            
            if('device_state' in addr_map['map'][batch]["data"]):
                self.error_init = True
                self.batch_device_state = i
                self.offset_device_state = (addr_map['map'][batch]["data"]['device_state']["offset"])

            i+=1

        self.active_alert_list = {}
        self.mqtt_alarm_list = []
        self.device_state = ""
        self.last_device_state = ""

    def isErrorPresent(self,error):
        for x in self.active_alert_list:
            if(error in x):
                return True
        
        return False
    
    def editErrorList(self,error_message,add):
        # print(self.device_state)
        if(add):
            if(error_message not in self.active_alert_list):
                error_dict = {}
                error_dict['timestamp'] = str(time.time())
                error_dict['vpp_id'] = ctrl.vpp_id
                error_dict['house_id'] = ctrl.site_id
                error_dict['device_id'] = str(17)
                error_dict['status'] = 'new'
                error_dict['severity'] = 'medium'
                error_dict['level'] = 'device'
                # error_dict['alert_message'] =  "fault"
                error_dict['alert_message'] = error_message
                ref = uuid.uuid4()
                error_dict['alert_ref'] = str(ref)
                error_dict['alert_code'] = str(self.status_code)
                self.alert_message.append(error_dict)
                self.mqtt_alarm_list.append(error_dict)
                self.active_alert_list[error_message] = str(ref)

        else:
            if(error_message in self.active_alert_list):
                error_dict = {}
                error_dict['timestamp'] = str(time.time())
                error_dict['vpp_id'] = ctrl.vpp_id
                error_dict['house_id'] = ctrl.site_id
                error_dict['device_id'] = str(17)
                error_dict['status'] = 'resolved'
                error_dict['severity'] = 'medium'
                error_dict['level'] = 'device'
                error_dict['alert_ref'] = self.active_alert_list[error_message]
                error_dict['error_message'] = error_message
                self.active_alert_list.pop(error_message)
                self.mqtt_alarm_list.append(error_dict)


    def errorDecode(self,data,device):
        if(not self.error_init):
            return
        try:
            #print(data)
            fault_code = data[self.batch_fault_code][self.offset_fault_code:self.offset_fault_code+self.fault_size]
            self.status_code = data[self.batch_device_state][self.offset_device_state]
            
            self.fault_code = BinaryPayloadDecoder.fromRegisters(fault_code,Endian.BIG).decode_32bit_uint()
            if(self.errror_map['Fault']['type'] == 'bitfield'):
                self.alert_message = []
                for i in self.errror_map['Fault']['codes']:
                    #print(self.errror_map['Fault']['codes'][i])
                    self.editErrorList(self.errror_map['Fault']['codes'][i],self.fault_code & (1 << int(i)))


                    
            # print(str(self.status_code))
            # print(self.errror_map["device_state"])
            # print(self.errror_map["device_state"]["codes"].keys())
            #print(self.status_code,self.fault_code)
            if(str(self.status_code) in self.errror_map["device_state"]):
                self.device_state = self.errror_map["device_state"][str(self.status_code)]
                # state = True if self.device_state != self.last_device_state else False
                # print(self.device_state)
                # print("into the device_state")
                self.editErrorList("FAULT", self.device_state == "FAULT")
                self.editErrorList("STANDBY", self.device_state == "STANDBY")
                self.editErrorList("TROTTLED", self.device_state == "TROTTLED")
                self.editErrorList("OFF", self.device_state == "OFF")
                self.editErrorList("SHUTTING_DOWN", self.device_state == "SHUTTING_DOWN")
                self.last_device_state = self.device_state
                
                
            # self.editErrorList("fault",str(self.device_state) == "FAULT")
            print("pre error decoded")
            self.sendMQTTErrorMessage(device)
            print("error decoded")
            #self.alert_message =

        except Exception as e:
            logging.warning(e)
                    
            
            #self.batch = batch
        pass


    def sendMQTTErrorMessage(self,device):
        # topic = 'alert/controller/' + str(device.device_id)
        topic = 'alert/controller/' + ctrl.controller_id

        # print(topic)

        #ccode to send the message
        while(len(self.mqtt_alarm_list) > 0):
            mqttmaster.mqtt_connection.mqttPublish(topic,self.mqtt_alarm_list.pop())
            


if __name__ == "__main__":
    addr_map = {}
    with open('../modbus_mappings/mappings.json') as mapfile:
        mbus_maps = json.load(mapfile)
        addr_map['map'] = mbus_maps["SG33KTL-M"]

        err = errRegistor(addr_map)


    