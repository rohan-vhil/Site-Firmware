# 

import json
import time
import threading
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusSequentialDataBlock, ModbusServerContext
from pymodbus.client import ModbusBaseClient as cltlib


class Device:
    def __init__(self, device_name, port, slave_id, params):
        self.device_name = device_name
        self.port = port
        self.slave_id = slave_id
        self.params = params  # Dictionary of all parameters to simulate (e.g. total_power)
        self.param_list = list(params.keys())

        # Load register mappings
        with open("modbus_registers.json") as f:
            all_regs = json.load(f)
            self.reading_registers = all_regs[device_name]

        # Init Modbus data store
        storeir = ModbusSequentialDataBlock(0x00, [0] * 60000)
        self.slave_context = ModbusSlaveContext(ir=storeir, hr=storeir)
        self.context = ModbusServerContext(slaves={self.slave_id: self.slave_context}, single=False)

    def run_server(self):
        print(f"[MODBUS] Starting server on port {self.port} for {self.device_name}")
        StartTcpServer(context=self.context, identity=None, address=("0.0.0.0", self.port))

    def run_loop(self):
        while True:
            for block in self.reading_registers:
                base_addr = self.reading_registers[block]["start_address"]
                for key, meta in self.reading_registers[block]["data"].items():
                    if key in self.params:
                        value = self.params[key]
                        encoder = getattr(cltlib.DATATYPE, meta["format"])
                        regs = cltlib.convert_to_registers(value, encoder)
                        addr = base_addr + meta["offset"]
                        self.context[self.slave_id].setValues(4, addr, regs)
            time.sleep(2)
