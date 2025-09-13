import sys
import json
sys.path.insert(0,"../")
# base_path = "/usr/local/bin/"
base_path = ""
sys.path.insert(0,base_path+'modbus_mappings/')
import enum
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
import time
import logging
sys.path.insert(0, 'edge_src/')
from mqtt_master import mqttmaster
import uuid
from control import control_base as ctrl
class error_type(enum.IntEnum) :
    fault= 0
    @classmethod
    def from_param(cls, obj):
        return int(obj) 


class controlRegistor:
    ds_batch: int
    ds_offset: int
    ds_size: int
    ds_format: None
    pl_batch: int
    pl_offset: int
    pl_size: int
    pl_format: None
    device_state: str
    control_map: dict
 
    def __init__(self,addr_map,part_num) -> None:
        i=0
        print(addr_map)
        with open(base_path + 'modbus_mappings/control_registers.json') as control_json:
            self.control_map = json.load(control_json)[part_num]

        print(self.control_map)
        for batch in self.control_map:
            #print(addr_map['map'][batch]["data"]["total_power"])

            if 'device_state' in self.control_map[batch]["data"]:
                self.ds_batch = i
                self.ds_offset = (self.control_map[batch]['data']['device_state']["offset"])
                self.ds_format = (self.control_map[batch]['data']['device_state']["format"])
                self.ds_size = (self.control_map[batch]['data']['device_state']["size"])

            if 'power_limit' in self.control_map[batch]["data"]:
                self.pl_batch = i
                self.pl_offset = (self.control_map[batch]['data']['power_limit']["offset"])
                self.pl_format = (self.control_map[batch]['data']['power_limit']["format"])
                self.pl_size = (self.control_map[batch]['data']['power_limit']["size"])

            i+=1



if __name__ == "__main__":
    addr_map = {}
    with open('../modbus_mappings/control_registers.json') as mapfile:
        mbus_maps = json.load(mapfile)
        addr_map['map'] = mbus_maps["SG33KTL-M"]

        err = controlRegistor(addr_map)


    