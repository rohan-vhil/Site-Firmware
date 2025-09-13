import sys
try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.client import ModbusSerialClient
    #from pymodbus import Framer
except Exception as e:
    from pymodbus.client.sync import ModbusSerialClient
    from pymodbus.client.sync import ModbusTcpClient

from datetime import datetime, time
import enum
import random
import time
import sys

sys.path.insert(0, "../")
sys.path.insert(0,'../control/')
from control import control_base as ctrl

# from auto_inverer_config import auto_cfg
from pymodbus.pdu import ModbusExceptions as mexcpt
from pymodbus.exceptions import ModbusIOException as mioexcept
from pymodbus.pdu import ExceptionResponse as mbusresp
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian
from pymodbus import framer

from typing import Union
import logging


class modbusTCPDetails:
    ip = None  # IP address of the device
    port = None
    address_map = None  # address map as provided by the manufacturer
    slave_id = 0


class modbusRTUdetails:
    port = None
    slave_id = 0
    address_map = None
    parity = 1
    stop_bits = 1
    baud = 9600


class read_result(enum.IntEnum):
    success = 0,
    fail_retry = 1,  # retry immediately
    fail_retry_later = 2,  # retry after some time
    fail_move = 3,  # read failed do not retry

    @classmethod
    def from_param(cls, obj):
        return int(obj)


class modbusRegType(enum.IntEnum):
    input = 0,
    holding = 1

    @classmethod
    def from_param(cls, obj):
        return int(obj)


class mbusErrorCodes(enum.IntEnum):

    no_error = 0,
    connection_error = 1,
    illegalAdrress = 2,
    illegalValue = 3,
    noresponse = 4,

    @classmethod
    def from_param(cls, obj):
        return int(obj)


class modbusTCPDevice(ctrl.systemDevice):
    modbusTCP_comm_details: modbusTCPDetails
    mbus_client: ModbusTcpClient
    device_connected: bool
    

    def __init__(self, devicetype, commtype,ip, port,slave_id=1,address_map={},ctrl_map={},cfg={}) -> None:
        super().__init__(devicetype, commtype,cfg)
        self.modbusTCP_comm_details = modbusTCPDetails()
        self.device_connected = False
        self.modbusTCP_comm_details.ip = ip
        self.modbusTCP_comm_details.port = port
        self.port = port
        self.slave_id = slave_id
        # self.modbusTCP_comm_details.address_map=address_map
        self.addr_map = address_map
        self.ctrl_map = ctrl_map
        self.mbus_client = ModbusTcpClient(ip, port=port)
        # if(self.mbus_client.connect()==False):
        #     self.device_connected = False

        # else:
        #     self.device_connected = True
        # #print(self.mbus_client.params)
        print("port is : ", self.modbusTCP_comm_details.port)

    def connect(self):
        if self.mbus_client.connect() == False:
            self.device_connected = False

        else:
            self.device_connected = True

        return True

    def close_connection(self):
        self.mbus_client.close()

        return False

    def writeDataToRegisters(self, reg_data_list,addr):
        
            #print(addr, reg_data_list)
            # print(self.modbusTCP_comm_details.address_map[addr])
            #int_data = int(reg_data_list[addr])
            #data_to_write = int_data if (int_data >= 0) else ((1 << 16) + int_data)
            # print(data_to_write)
            try:
                self.mbus_client.write_registers(
                    addr, reg_data_list
                )
            except Exception as e:
                logging.warning("unable to write data "+str(e))
    def writeDataToCtrlRegisters(self, reg_data):
        try:
            builder = BinaryPayloadBuilder(byteorder=getattr(Endian, reg_data["bo"]), wordorder=getattr(Endian, reg_data["wo"]))
            attribute = getattr(builder, reg_data["format"])
            # builder.add_16bit_float(12.34)
            # payload = getattr(builder, attribute(reg_data["value"])).build()
            print(attribute(int(reg_data["value"])))
            payload = builder.build()
            print(payload)
            print(reg_data["address"])
            x = self.mbus_client.write_register(
                    reg_data["address"], payload[0], skip_encode=True, slave=1
                )
            print(x) 
            pass
        except Exception as e:
            print(e)
            logging.error(str(e))

class modbusRTUDevice(ctrl.systemDevice):
    modbusRTU_comm_details: modbusRTUdetails
    mbus_client: ModbusSerialClient
    addr_map: dict

    def __init__(
        self,
        devicetype,
        commtype,
        address_map,
        control_map,
        port,
        parity,
        stop_bits,
        baud,
        slave_id=0,
        rated_power=15000,cfg={}
    ) -> None:
        super().__init__(devicetype, commtype,cfg)
        self.modbusRTU_comm_details = modbusRTUdetails()
        # self.modbusRTU_comm_details.address_map = address_map
        self.addr_map = address_map
        self.ctrl_map = control_map
        self.modbusRTU_comm_details.port = port
        self.modbusRTU_comm_details.parity = parity
        self.modbusRTU_comm_details.baud = baud
        self.modbusRTU_comm_details.slave_id = slave_id
        self.slave_id = slave_id
        self.modbusRTU_comm_details.stop_bits = stop_bits
        # print("port : ",port)
        if sys.version_info.major < 3 or sys.version_info.minor < 10:
            self.mbus_client = ModbusSerialClient(
                method="rtu",
                port=self.modbusRTU_comm_details.port,
                baudrate=baud,
                timeout=1,
                parity=parity,
            )
        else:
            self.mbus_client = ModbusSerialClient(
                port, framer.FramerType.RTU, baud, 8, parity, stop_bits
            )
        # if(self.mbus_client.connect()==False):
        #     self.device_connected = False

        # else:
        #     self.device_connected = True

    def connect(self):
        #print("Modbus is connected...!!")
        if self.mbus_client.connect() == False:
            self.device_connected = False

        else:
            self.device_connected = True

        return True

    def close_connection(self):
        self.mbus_client.close()
        return False

    def writeDataToRegisters(self, reg_data_list,addr):
        
            #print(addr, reg_data_list)
            # print(self.modbusTCP_comm_details.address_map[addr])
            #int_data = int(reg_data_list[addr])
            #data_to_write = int_data if (int_data >= 0) else ((1 << 16) + int_data)
            # print(data_to_write)
            try:
                self.mbus_client.write_registers(
                    addr, reg_data_list
                )
            except Exception as e:
                logging.warning("unable to write data "+str(e))
    def writeDataToCtrlRegisters(self, reg_data):
        try:
            builder = BinaryPayloadBuilder(byteorder=getattr(Endian, reg_data["bo"]), wordorder=getattr(Endian, reg_data["wo"]))
            attribute = getattr(builder, reg_data["format"])
            # builder.add_16bit_float(12.34)
            # payload = getattr(builder, attribute(reg_data["value"])).build()
            print(attribute(int(reg_data["value"])))
            payload = builder.build()
            print(payload)
            print(reg_data["address"])
            x = self.mbus_client.write_register(
                    reg_data["address"], payload[0], skip_encode=True, unit=0, slave=0
                )
            print(x)
            pass
        except Exception as e:
            print(e)
            logging.error(str(e))


sungrow_address_map = {
    "device_type": 5000,
    "nominal_power": 5001,
    "output_type": 5002,
    "power_limit_enable": 5007,
    "power_limit": 5008,
}

sunspec_address_map_1 = {
    "SunSidentifier1": 40001,
    "SunSidentifier2": 40002,
    "commonblockidentifer": 40003,
    "I_AC_Current": 40072,
    "I_AC_CurrentA": 40073,
    "I_AC_CurrentB": 40074,
    "I_AC_CurrentC": 40075,
    "I_AC_Current_SF": 40076,
    "I_AC_VoltageAB": 40077,
    "I_AC_VoltageBC": 40078,
    "I_AC_VoltageCA": 40079,
    "I_AC_VoltageAN": 40080,
    "I_AC_VoltageBN": 40081,
    "I_AC_VoltageCN": 40082,
    "I_AC_Voltage_SF": 40083,
    "AC Active_power": 40084,
    "Total energy": [40094, 40095],
    "AC Active_powerSetPct": 50000,
}

delta_inverter_map = {
    "I_AC_VoltageAN": 1057,
    "I_AC_Current": 1058,
    "AC Active_power": 1059,
    "Total energy1": 53252,
    "Total energy2": 53253,
}

part_list = []


class power_direction(enum.IntEnum):
    out = (0,)
    inp = (1,)
    bi = 2

    @classmethod
    def from_param(cls, obj):
        return int(obj)


class PowerDevice:
    address_map = None
    direction = None
    ip = None
    port = None
    mbus_client = None

    def __init__(self, address_map, power_direction, ip, port) -> None:
        self.address_map = address_map
        self.direction = power_direction
        self.ip = ip
        self.port = port
        self.mbus_client = ModbusTcpClient(self.ip, port=self.port)
        # self.mbus_client.connect()

#16 bit to int
def bytes_to_registers(data):
    registers = []
    for x in data:
        for i in range(0, len(x), 2):
            register = int.from_bytes(x[i : i + 2], byteorder="little")
            registers.append(register)
    return registers


def writeModbusData(device: Union[modbusRTUDevice, modbusTCPDevice], address, data):
    # payload = bytes_to_registers(data)
    payload = []
    try:
        payload = bytes_to_registers(data)
        # print(payload,address)
        device.mbus_client.write_registers(
            address, values=payload, slave=device.slave_id, unit=device.slave_id
        )
    except Exception as e:
        logging.warning(str(e))


#read input register and holding register data from modbus 
def getData(addrmap:dict,device:Union[modbusRTUDevice, modbusTCPDevice]):
    data = []
    MAX_LENGTH = 125
    
    try:
        #print(device.slave_id,addrmap)
        for block in addrmap:
           # if(device.device_type == 2):
                #print(mode,": ",addrmap)
            # logging.info(str(block) + " : " + str(device.addr_map['map'][block]['Length']))
            length = addrmap[block]["Length"]
            start_addr = addrmap[block]["start_address"]
            remaining_length = length
            reg_type = addrmap[block]["registers"]
            # logging.info(str(block) + " : " + str(device.addr_map['map'][block]['Length']) + " " + reg_type + "  " + str(start_addr))
            if reg_type == "ir":
                read_func = device.mbus_client.read_input_registers

            else:
                read_func = device.mbus_client.read_holding_registers
            # if(length > MAX_LENGTH):
            #print("connect device",device.connect())
            if(device.connect()):
                #print("device is connected",read_func)
                data.append([])
                while remaining_length > MAX_LENGTH:
                    val = read_func(
                        start_addr, MAX_LENGTH, slave=device.slave_id
                    )
                    #print("val read : ", val)
                    if val.isError():
                        logging.warning("error : {}".format(val) + str(start_addr))
                    data[-1] += val.registers
                    remaining_length = remaining_length - MAX_LENGTH
                    start_addr = start_addr + MAX_LENGTH

                val = read_func(
                    start_addr,
                    remaining_length,
                    slave=device.slave_id
                )
                #print("val read : ",val)
                if val.isError():
                    logging.warning("error : {}".format(val) + str(start_addr))

                data[-1] += val.registers
                device.read_error = False
                device.close_connection()


            else:
                print("device is not connected : ", device.device_connected)
    except Exception as e:
        device.read_error = True
        #print("modbus read error ",e)
        logging.error("modbus read error" + str(e) + str(device.device_type))
        # print(data)
        # if(values.isError()):

        # data.append(values)
    #print(data)
    return data


def getModbusData(device: Union[modbusRTUDevice, modbusTCPDevice]):
    pass
    
    modbusdata = {}
    MAX_LENGTH = 125
    
    modbusdata['read'] = (getData(device.addr_map['map'],device))
    #print(modbusdata['read'])
    modbusdata['control'] = (getData(device.ctrl_map['map'],device))
    if(device.device_type == 0):
    #   print(device.addr_map)
       # print(device.ctrl_map)
       pass
    return modbusdata
    
    try:
        # print(device.slave_id)
        for block in device.addr_map["map"]:
            # print(block)
            # logging.info(str(block) + " : " + str(device.addr_map['map'][block]['Length']))
            length = device.addr_map["map"][block]["Length"]
            start_addr = device.addr_map["map"][block]["start_address"]
            remaining_length = length
            reg_type = device.addr_map["map"][block]["registers"]
            # logging.info(str(block) + " : " + str(device.addr_map['map'][block]['Length']) + " " + reg_type + "  " + str(start_addr))
            if reg_type == "ir":
                read_func = device.mbus_client.read_input_registers

            else:
                read_func = device.mbus_client.read_holding_registers
            # if(length > MAX_LENGTH):
            data.append([])
            while remaining_length > MAX_LENGTH:
                val = read_func(
                    start_addr, MAX_LENGTH, slave=device.slave_id
                )
                if val.isError():
                    logging.warning("error : {}".format(val) + str(start_addr))
                data[-1] += val.registers
                remaining_length = remaining_length - MAX_LENGTH
                start_addr = start_addr + MAX_LENGTH

            val = read_func(
                start_addr,
                remaining_length,
                slave=device.slave_id,
                unit=device.slave_id,
            )
            if val.isError():
                logging.warning("error : {}".format(val) + str(start_addr))

            data[-1] += val.registers
            device.read_error = False
    except Exception as e:
        device.read_error = True
        logging.error("modbus read error" + str(e))
        # print(data)
        # if(values.isError()):

        # data.append(values)
    # print(data)
    return data


def getModbusTCPData(device: modbusTCPDevice):
    data = {}
    read_data = []
    device.mbus_client.connect()
    # modbusTCPDevice.mbus_client.read_holding_registers(modbusTCPDevice.modbusTCP_comm_details.address_map[addr]-1,1)
    # print("device port : ", device.port,",  type : ", device.device_type)
    for addr in device.modbusTCP_comm_details.address_map:
        try:
            if type(device.modbusTCP_comm_details.address_map[addr]) == list:
                ln = len(device.modbusTCP_comm_details.address_map[addr])
                # print(addr)
                read_data = device.mbus_client.read_holding_registers(
                    device.modbusTCP_comm_details.address_map[addr][0], count=ln
                )
            else:
                read_data = device.mbus_client.read_holding_registers(
                    device.modbusTCP_comm_details.address_map[addr], 1
                )
            error = read_data.isError()
            # print(read_data.registers)
        except Exception as e:
            logging.warning("modbus tcp exception error : " + str(e))
            error = True

        data[addr] = "ReadError" if (error) else read_data.registers
        data[addr + "_readError"] = error
        # data[addr]=device.mbus_client.read_holding_registers(device.modbusTCP_comm_details.address_map[addr]-1,1).registers[0]
        # data[addr] = "ReadError" if(error) else read_data.registers
    device.mbus_client.close()
    # print(data)
    return data


def getModbusRTUData(device: modbusRTUDevice):
    data = {}
    read_data = []
    device.mbus_client.connect()
    for addr in device.modbusRTU_comm_details.address_map:
        try:
            if type(device.modbusRTU_comm_details.address_map[addr]) == list:
                ln = len(device.modbusRTU_comm_details.address_map[addr])
                # print(addr)
                read_data = device.mbus_client.read_holding_registers(
                    device.modbusRTU_comm_details.address_map[addr][0],
                    count=ln,
                    unit=1,
                    slave=1,
                )
            else:
                device.mbus_client.socket.reset_input_buffer()
                device.mbus_client.socket.reset_output_buffer()
                time.sleep(1)
                read_data = device.mbus_client.read_holding_registers(
                    device.modbusRTU_comm_details.address_map[addr], 1, unit=1, slave=1
                )
            # data[addr]=device.mbus_client.read_holding_registers(device.modbusTCP_comm_details.address_map[addr]-1,1).registers[0]
            error = read_data.isError()
        except Exception as e:
            logging.log("modbus rtu exception error : " + str(e))
            error = True
        data[addr] = "ReadError" if (error) else read_data.registers
        data[addr + "_readError"] = error

    device.mbus_client.close()
    # print(data)
    return data


def partNumberToddressMap(part_num):
    if part_num == "solar-edge":
        return sunspec_address_map_1

    elif part_num == "delta":
        return delta_inverter_map


def init_device(dict_name, direction, ip, port):
    part_list.append(PowerDevice(dict_name, direction, ip, port))


def read_data_input(device_num, data_name):
    wr = part_list[device_num].mbus_client.read_input_registers(
        part_list[device_num].address_map[data_name] - 1, 1
    )
    return wr


def read_data_holding(device_num, data_name):
    wr = part_list[device_num].mbus_client.read_holding_registers(
        part_list[device_num].address_map[data_name] - 1, 1
    )
    return wr


def write_data(device_num, data_name, data, i=-1):
    # if(type(part_list[device_num].address_map[data_name]) == list):

    if i >= 0:
        write_addr = part_list[device_num].address_map[data_name][i]
    else:
        write_addr = part_list[device_num].address_map[data_name]

    wr = part_list[device_num].mbus_client.write_registers(write_addr - 1, data)


def tryReadingModbusRegister(
    client: Union[ModbusSerialClient, ModbusTcpClient],
    addr: int,
    count: int = 1,
    slave_id: int = 0,
    unit: int = 0,
) -> tuple:
    try:
        # print("address : ",addr)
        rr = client.read_holding_registers(
            address=addr, count=count, slave=slave_id, unit=unit
        )
    except Exception as e:
        # print("error reading registers",e)
        return (mbusErrorCodes.connection_error, -1)
    if rr.isError():
        # print("type is : ",type(rr))
        if type(rr) == mioexcept:
            return (mbusErrorCodes.noresponse, -1)

        elif type(rr) == mbusresp:
            # print("modbus exception",rr.exception_code)
            if rr.exception_code == mexcpt.IllegalAddress:
                return (mbusErrorCodes.illegalAdrress, -1)

    else:
        return (mbusErrorCodes.no_error, rr.registers)
