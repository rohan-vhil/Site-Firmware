import enum
import asyncio
import math
import logging
import time
from control import error_reporting as err
from control import control_der as ctrl_der
from modbus_master import modbusmasterapi as mbus
import sys
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian
sys.path.insert(0,'../')
import json
import path_config
from typing import List, Optional, Dict, Any, Set

default_Ts = 3
default_Ki = 0.0001
default_Kp = 0.00001
vpp_id: int = 0
site_id: int = 0
mqtt_ip: str = "test.mosquitto.org"
controller_id: str
per_phase_data =['V','I','P','Q','S','En']
io_data = ['digital', 'analog']

agg_data = ['Pf','total_power','total_energy','voltage','acfreq','temperature','apparent_power','reactive_power','input_power',"SoC","SoH",'current','import_energy','export_energy','charging_energy','discharging_energy']
data_decode = {
    "V" : "voltage",
    "I" : "current",
    "P" : "power",
    "Q" : "Q",
    "S" : "S",
    "En" : "energy"
}

component_data = {
    "mppt_voltage": [],
    "mppt_current": [],
    "mppt_power": [],
    "string_voltage": [],
    "string_current": [],
    "string_power": [],
    "cell_voltage": []
}


class deviceType(enum.IntEnum):
    solar = 0
    battery = 1
    meter = 2
    EV = 3
    DG=4
    grid = 5
    IO = 6

    @classmethod
    def from_param(cls, obj):
        return int(obj)


class modeSrc(enum.IntEnum):
    direct_comm = 0
    from_schedule = 1
    no_src = 2

    @classmethod
    def from_param(cls, obj):
        return int(obj)


class commType(enum.IntEnum):
    modbus_tcp = 0
    modbus_rtu = 1
    can = 2
    api = 3
    ccs2 = 4
    gpio = 5
    none = 6

    @classmethod
    def from_param(cls, obj):
        return int(obj)


class factorType(enum.IntEnum):
    mf_value = 0
    mf_address = 1
    sf_value = 2
    sf_address = 3

    @classmethod
    def from_param(cls, obj):
        return int(obj)


class systemOperatingModes(enum.IntEnum):
    const_power = 0
    pv_charge_only_mode = 1
    full_backup = 2
    max_export = 3
    max_import = 4
    full_backup_with_zn = 5
    gen_limit = 6
    dr_command = 7
    daily_peak_th_base = 8
    daily_peak_time_base = 9
    export_limit = 10
    dg_pv_sync = 11
    schedule = 10
    none = 11

    @classmethod
    def from_param(cls, obj):
        return int(obj)


deviceType_l2e = {
    "solar-inverter": deviceType.solar,
    "battery": deviceType.battery,
    "meter": deviceType.meter,
    "EV": deviceType.EV,
    "DG" : deviceType.DG,
    "grid" : deviceType.grid,
    "IO":deviceType.IO

}

commType_l2e = {
    "modbus-tcp": commType.modbus_tcp,
    "modbus-rtu": commType.modbus_rtu,
    "CAN": commType.can,
    "API": commType.api,
    "CCS2": commType.ccs2,
    "gpio": commType.gpio
}

operatingMode_l2e = {
    "pv_charge_only": systemOperatingModes.pv_charge_only_mode,
    "net_zero": systemOperatingModes.const_power,
    "power_backup": systemOperatingModes.full_backup,
    "max_export": systemOperatingModes.max_export,
    "gen_limit": systemOperatingModes.gen_limit,
    "none" : systemOperatingModes.none
}
deviceType_e2s = {
    deviceType.solar : "inverter",
    deviceType.battery : "battery",
    deviceType.meter : "meter",
    deviceType.EV : "EV",
    deviceType.DG: "DG",
    deviceType.grid: "grid",
    deviceType.IO: "IO"
}

def scaleData(data, scale_factor):
    x = 0

    if type(data) == list:
        for i in range(len(data)):
            x = x + (data[len(data) - i - 1] << i * 16)

    else:
        x = data

    return x * scale_factor

class dataModel:
    valueFromReg: Any
    value: float
    batch_start_addr: int
    data: Any
    size: int
    decoderFunc: Optional[str]
    encoderFunc: Optional[str]
    factorDecoderFunc: Optional[str]
    factor_type: factorType
    factor_value: float
    has_en:bool
    en_block :int
    en_offset :int
    data_error: bool
    prev_correct_value: float
    block_num: int
    offset: int
    factor_block: int
    factor_offset: int
    byteorder: str
    wordorder: str
    model_present : bool
    en_start_addr:int
    mode_offset :int
    mode_block : int
    mode_start_addr : int
    has_mode : bool
    addr: str

    def __init__(self, addr: str="", valuefunc=scaleData, scale_factor=1) -> None:
        self.valueFromReg = valuefunc
        self.addr = addr
        self.value = 0.0
        self.factor_type = factorType.mf_value
        self.factor_value = float(scale_factor)
        self.batch_start_addr = 0
        self.data = None
        self.size = 0
        self.decoderFunc = None
        self.encoderFunc = None
        self.factorDecoderFunc = None
        self.has_en=False
        self.en_block =0
        self.en_offset = 0
        self.data_error = False
        self.prev_correct_value = 0.0
        self.block_num = 0
        self.offset = 0
        self.factor_block =0
        self.factor_offset = 0
        self.byteorder = "BIG"
        self.wordorder = "LITTLE"
        self.model_present = False
        self.en_start_addr=0
        self.mode_offset = 0
        self.mode_block = 0
        self.mode_start_addr = 0
        self.has_mode = False


    def getData(self, data_input: Dict[int, List[int]]) -> None:
        try:
            if self.data is None or not isinstance(self.data, list) or not self.data :
                return
            decoded = BinaryPayloadDecoder.fromRegisters(self.data, wordorder=getattr(Endian, self.wordorder), byteorder=getattr(Endian, self.byteorder))
            if(self.decoderFunc == None):
                return
            else:
                tmp = getattr(decoded, self.decoderFunc)()

            if self.factor_type == factorType.mf_value:
                self.value = tmp * self.factor_value
            elif self.factor_type == factorType.sf_address:
                if self.factorDecoderFunc and data_input and self.factor_block in data_input and isinstance(data_input[self.factor_block], list) and self.factor_offset < len(data_input[self.factor_block]):
                    factor_reg_data = [data_input[self.factor_block][self.factor_offset]]
                    decoded_factor = BinaryPayloadDecoder.fromRegisters(factor_reg_data, wordorder=getattr(Endian, self.wordorder), byteorder=getattr(Endian, self.byteorder))
                    self.value = tmp * (10 ** getattr(decoded_factor, self.factorDecoderFunc)())
                else:
                    self.value = tmp
            else:
                self.value = tmp
        except Exception as e:
            logging.warning(
                str(e)
                + str(" block : ")
                + str(self.block_num)
                + str(" offset : ")
                + str(self.offset)
            )

    def decodeFactor(self):
        self.factor_value = -1

    def getFactors(self, data_input: Dict[int, List[int]]):
        try:
            if self.factor_type == factorType.sf_address:
                if self.factorDecoderFunc and data_input and self.factor_block in data_input and isinstance(data_input[self.factor_block], list) and self.factor_offset < len(data_input[self.factor_block]):
                    factor_reg_data = [data_input[self.factor_block][self.factor_offset]]
                    decoded_factor = BinaryPayloadDecoder.fromRegisters(factor_reg_data, Endian.BIG)
                    self.factor_value = getattr(decoded_factor, self.factorDecoderFunc)()
        except Exception as e:
            logging.warning(str(e) + str(data_input))

    def encode(self):
        data_to_encode = self.value
        builder = BinaryPayloadBuilder(byteorder=getattr(Endian, self.byteorder), wordorder=getattr(Endian, self.wordorder))

        if not self.decoderFunc:
            logging.warning(f"No decoderFunc set for encoding, cannot determine encoder method for {self.addr}")
            return None

        val_to_encode = 0
        if self.factor_type == factorType.sf_address:
            power_val = 10**self.factor_value
            if power_val == 0:
                logging.warning(f"Factor (10^{self.factor_value}) is zero, cannot encode by division for {self.addr}")
                return None
            val_to_encode = int(data_to_encode / power_val)
        elif self.factor_type == factorType.mf_value:
            if self.factor_value == 0:
                logging.warning(f"Factor is zero, cannot encode by division for {self.addr}")
                return None
            val_to_encode = int(data_to_encode / self.factor_value)
        else:
            val_to_encode = int(data_to_encode)

        encoder_method_name = self.decoderFunc.replace("decode_", "add_")
        if hasattr(builder, encoder_method_name):
            getattr(builder, encoder_method_name)(val_to_encode)
        else:
            logging.warning(f"Encoder method {encoder_method_name} not found in BinaryPayloadBuilder for decoder {self.decoderFunc} for {self.addr}")
            return None
        return builder.build()


class measuredData:
    V: List[dataModel]
    I: List[dataModel]
    P: List[dataModel]
    Q: List[dataModel]
    S: List[dataModel]
    En: List[dataModel]
    
    digital: List[Any]
    analog: List[Any]
    
    phase: int
    addr_map: dict
    validated: bool
    rev_correct_en: float

    Pf: Optional[dataModel]
    total_power: Optional[dataModel]
    total_energy: Optional[dataModel]
    voltage: Optional[dataModel]
    acfreq: Optional[dataModel]
    temperature: Optional[dataModel]
    apparent_power: Optional[dataModel]
    reactive_power: Optional[dataModel]
    input_power: Optional[dataModel]
    SoC: Optional[dataModel]
    SoH: Optional[dataModel]
    current: Optional[dataModel]
    import_energy: Optional[dataModel]
    export_energy: Optional[dataModel]
    today_energy: Optional[dataModel]
    charging_energy: Optional[dataModel]
    discharging_energy: Optional[dataModel]

    mppt_voltage: List[Any]
    mppt_current: List[Any]
    mppt_power: List[Any]
    string_voltage: List[Any]
    string_current: List[Any]
    string_power: List[Any]
    cell_voltage: List[Any]

    def __init__(self, phase: int = 1) -> None:
        self.phase = phase
        self.V = []
        self.I = []
        self.P = []
        self.Q = []
        self.S = []
        self.En = []
        self.digital = []
        self.analog = []
        
        self.mppt_voltage = []
        self.mppt_current = []
        self.mppt_power = []
        self.string_voltage = []
        self.string_current = []
        self.string_power = []
        self.cell_voltage = []

        self.addr_map = {}
        self.validated = False
        self.rev_correct_en = 0.0

        self.Pf = None
        self.total_power = None
        self.total_energy = None
        self.voltage = None
        self.acfreq = None
        self.temperature = None
        self.apparent_power = None
        self.reactive_power = None
        self.input_power = None
        self.SoC = None
        self.SoH = None
        self.current = None
        self.import_energy = None
        self.export_energy = None
        self.today_energy = None
        self.charging_energy = None
        self.discharging_energy = None


class measuredBatteryData:
    pass

def getTwosComp(data):
    data = int(data)
    return data if (data < 0x8000) else data - (1 << 16)


class controlData:
    power_pct_stpt: dataModel
    power_stpt: dataModel
    device_state: dataModel
    poweer_lt : dataModel

    def __init__(self) -> None:
        self.power_pct_stpt = dataModel("power stpt", scaleData, 1)
        self.device_state = dataModel("device state", scaleData, 1)
        self.poweer_lt = dataModel("power_limit",scaleData,1)


class systemDevice:
    device_type: deviceType
    measured_data: measuredData
    control_data: controlData
    comm_type: commType
    comm_details: Any
    rated_power: float
    stptCurve: Any
    device_id: int
    addr_map: dict
    ctrl_map:dict
    err_registers: Optional[err.errRegistor]
    ctrl_registers : Optional[ctrl_der.controlRegistor]
    read_error: bool
    num_phases :int
    phase :str
    connected_to : str

    def __init__(self, devicetype: deviceType, commtype: commType, cfg: Dict[str, Any], rated_power: float=3800) -> None:
        self.device_type = devicetype
        self.comm_type = commtype
        self.rated_power = rated_power
        self.num_phases = cfg.get("num_phases", 1)
        self.device_id = cfg.get("device_id", 0)
        self.addr_map = {}
        self.ctrl_map = {}
        self.err_registers = None
        self.ctrl_registers = None
        self.phase = "A"
        self.connected_to = ""
        self.comm_details = None
        self.stptCurve = None


        if devicetype == deviceType.solar:
            self.stptCurve = PVCurveFunc
            system_operating_details.agg_pv_rated += rated_power
        elif devicetype == deviceType.battery:
            self.stptCurve = batteryCurveFunc
            system_operating_details.agg_batt_rated += rated_power

        self.measured_data = measuredData(phase=self.num_phases)
        self.control_data = controlData()
        self.read_error = False

        if self.device_type == deviceType.meter:
            tech_details = cfg.get("tech_details", {})
            self.connected_to = str(tech_details.get("connected_to", ""))


    def createMapForVar(self, var: dataModel, batch: str, i: int, var_name: str):
        var.model_present = True
        x = self.addr_map["map"][batch]["data"][var_name]
        var.byteorder = self.addr_map["map"][batch].get("byteorder", "BIG")
        var.wordorder = self.addr_map["map"][batch].get("wordorder", "LITTLE")
        var.block_num = i
        var.offset = x["offset"]
        var.size = x["size"]
        var.batch_start_addr = self.addr_map["map"][batch]["start_address"]

        if "s_f" in x and x["s_f"] != "NA":
            if type(x["s_f"]) == str:
                var.factor_type = factorType.sf_address
                j = 0
                for section_name, section_content in self.addr_map["map"].items():
                    if x["s_f"] in section_content.get("data", {}):
                        var.factor_block = j
                        var.factor_offset = section_content["data"][x["s_f"]]["offset"]
                        var.factorDecoderFunc = section_content["data"][x["s_f"]]["format"]
                        break
                    j = j + 1

        if "m_f" in x and x["m_f"] != "NA":
            if type(x["m_f"]) == float or type(x["m_f"]) == int:
                var.factor_type = factorType.mf_value
                var.factor_value = float(x["m_f"])

        var.decoderFunc = x["format"]


    def createMapForCtrlVar(self, var: dataModel, batch: str, i: int, var_name: str):
        var.model_present = True
        x = self.ctrl_map["map"][batch]["data"][var_name]
        var.byteorder = self.ctrl_map["map"][batch].get("byteorder", "BIG")
        var.wordorder = self.ctrl_map["map"][batch].get("wordorder", "LITTLE")
        var.block_num = i
        var.offset = x["offset"]
        var.size = x["size"]
        var.batch_start_addr = self.ctrl_map["map"][batch]["start_address"]

        if "s_f" in x and x["s_f"] != "NA":
            if type(x["s_f"]) == str:
                j = 0
                for section_name, section_content in self.ctrl_map["map"].items():
                    if x["s_f"] in section_content.get("data", {}):
                        var.factor_block = j
                        var.factor_offset = section_content["data"][x["s_f"]]["offset"]
                        var.factorDecoderFunc = section_content["data"][x["s_f"]]["format"]
                        break
                    j = j + 1

        if "m_f" in x and x["m_f"] != "NA":
            if type(x["m_f"]) == float or type(x["m_f"]) == int:
                var.factor_type = factorType.mf_value
                var.factor_value = float(x["m_f"])

        if "switch_register" in x and x["switch_register"] != "NA" and x["switch_register"] != "":
            if x["switch_register"] in self.ctrl_map["map"][batch].get("data",{}):
                var.en_offset = self.ctrl_map["map"][batch]["data"][x["switch_register"]]["offset"]
                var.en_block = i
                var.en_start_addr = self.ctrl_map["map"][batch]["start_address"]
            else:
                logging.warning(f"Switch register '{x['switch_register']}' not found in control map for {var_name}")


        if "mode_reg" in x and x["mode_reg"] != "" and x["mode_reg"] != "NA":
            if x["mode_reg"] in self.ctrl_map["map"][batch].get("data",{}):
                var.mode_offset = self.ctrl_map["map"][batch]["data"][x["mode_reg"]]["offset"]
                var.mode_start_addr = self.ctrl_map["map"][batch]["start_address"]
                var.mode_block = i
                var.has_mode = True
            else:
                logging.warning(f"Mode register '{x['mode_reg']}' not found in control map for {var_name}")

        var.decoderFunc = x["format"]


    def createErrorMap(self, part_num: str):
        if err:
             self.err_registers = err.errRegistor(self.addr_map, part_num)

    def createControlMap(self, part_num: str):
        try:
            with open('modbus_mappings/control_registers.json') as mapfile:
                self.ctrl_map['map'] = json.load(mapfile)[part_num]
        except FileNotFoundError:
            logging.error("modbus_mappings/control_registers.json not found.")
            self.ctrl_map['map'] = {}
        except KeyError:
            logging.error(f"Part number {part_num} not found in control_registers.json.")
            self.ctrl_map['map'] = {}
        except Exception as e:
            logging.error(f"Failed to load control map for {part_num}: {e}")
            self.ctrl_map['map'] = {}


    def createMeasureMap(self,part_num: str):
        try:
            with open('modbus_mappings/mappings.json') as mapfile:
                self.addr_map['map'] = json.load(mapfile)[part_num]
        except FileNotFoundError:
            logging.error("modbus_mappings/mappings.json not found.")
            self.addr_map['map'] = {}
        except KeyError:
            logging.error(f"Part number {part_num} not found in mappings.json.")
            self.addr_map['map'] = {}
        except Exception as e:
            logging.error(f"Failed to load measure map for {part_num}: {e}")
            self.addr_map['map'] = {}


    def createMeasureRegisterMap(self):
        i = 0
        if not self.addr_map or 'map' not in self.addr_map or not isinstance(self.addr_map['map'], dict):
            return

        for batch_name, batch_content in self.addr_map["map"].items():
            if not isinstance(batch_content, dict) or "data" not in batch_content or not isinstance(batch_content["data"], dict):
                continue
            
            batch_data_map = batch_content["data"]

            if "L1_voltage" in batch_data_map:
                dm = dataModel()
                self.measured_data.V.append(dm)
                self.createMapForVar(dm, batch_name, i, "L1_voltage")

            if self.num_phases > 1 and "L2_voltage" in batch_data_map:
                dm = dataModel()
                self.measured_data.V.append(dm)
                self.createMapForVar(dm, batch_name, i, "L2_voltage")

            if self.num_phases > 2 and "L3_voltage" in batch_data_map:
                dm = dataModel()
                self.measured_data.V.append(dm)
                self.createMapForVar(dm, batch_name, i, "L3_voltage")

            if "L1_power" in batch_data_map:
                dm = dataModel()
                self.measured_data.P.append(dm)
                self.createMapForVar(dm, batch_name, i, "L1_power")

            if self.num_phases > 1 and "L2_power" in batch_data_map:
                dm = dataModel()
                self.measured_data.P.append(dm)
                self.createMapForVar(dm, batch_name, i, "L2_power")

            if self.num_phases > 2 and "L3_power" in batch_data_map:
                dm = dataModel()
                self.measured_data.P.append(dm)
                self.createMapForVar(dm, batch_name, i, "L3_power")
            
            current_agg_data_list = agg_data
            if hasattr(self.measured_data, "today_energy"): # If today_energy is a defined attribute
                 if "today_energy" not in current_agg_data_list : # And if user wants it processed via this loop
                     # This implies today_energy should be added to agg_data list if it needs this processing
                     pass


            for x in current_agg_data_list: # Iterate through the global agg_data list
                if hasattr(self.measured_data, x) and x in batch_data_map:
                     dm_attr = dataModel()
                     setattr(self.measured_data, x, dm_attr)
                     self.createMapForVar(dm_attr, batch_name, i, x)
            i += 1


    def createControlRegisterMap(self):
        i=0
        if not self.ctrl_map or 'map' not in self.ctrl_map or not isinstance(self.ctrl_map['map'], dict):
            return

        for batch_name, batch_content in self.ctrl_map['map'].items():
            if not isinstance(batch_content, dict) or "data" not in batch_content or not isinstance(batch_content["data"], dict):
                continue
            batch_data_map = batch_content["data"]

            if('power_limit' in batch_data_map):
                self.createMapForCtrlVar(self.control_data.poweer_lt,batch_name,i,"power_limit")
            if('power_limit_pct' in batch_data_map):
                self.createMapForCtrlVar(self.control_data.power_pct_stpt,batch_name,i,"power_limit_pct")
            i+=1


    def encodeWrite(self, msg_json:dict):
        if msg_json.get("param") == "active_power":
            value_str = msg_json.get('value')
            if value_str is None:
                logging.warning("No value provided for active_power setpoint.")
                return
            
            try:
                target_power_value = float(value_str)
            except ValueError:
                logging.error(f"Invalid numeric value for active_power: {value_str}")
                return

            if self.control_data.poweer_lt.model_present:
                self.control_data.poweer_lt.value = target_power_value
                encoded_payload = self.control_data.poweer_lt.encode()
                if encoded_payload is not None and mbus is not None:
                    if self.control_data.poweer_lt.has_mode:
                        mode_builder = BinaryPayloadBuilder(byteorder=getattr(Endian, self.control_data.poweer_lt.byteorder), wordorder=getattr(Endian, self.control_data.poweer_lt.wordorder))
                        mode_builder.add_16bit_uint(1)
                        mode_payload = mode_builder.build()
                        self.writeDataToRegisters(mbus.bytes_to_registers(mode_payload),self.control_data.poweer_lt.mode_start_addr + self.control_data.poweer_lt.mode_offset)

                    en_builder = BinaryPayloadBuilder(byteorder=getattr(Endian, self.control_data.poweer_lt.byteorder), wordorder=getattr(Endian, self.control_data.poweer_lt.wordorder))
                    en_builder.add_16bit_uint(1)
                    en_payload = en_builder.build()
                    self.writeDataToRegisters(mbus.bytes_to_registers(en_payload),self.control_data.poweer_lt.en_start_addr + self.control_data.poweer_lt.en_offset)
                    self.writeDataToRegisters(mbus.bytes_to_registers(encoded_payload),self.control_data.poweer_lt.batch_start_addr + self.control_data.poweer_lt.offset)

            elif self.control_data.power_pct_stpt.model_present:
                if self.rated_power == 0:
                    logging.warning("Rated power is 0, cannot calculate percentage setpoint.")
                    return
                self.control_data.power_pct_stpt.value = target_power_value * 100.0 / self.rated_power
                encoded_payload = self.control_data.power_pct_stpt.encode()
                if encoded_payload is not None and mbus is not None:
                    en_builder = BinaryPayloadBuilder(byteorder=getattr(Endian, self.control_data.power_pct_stpt.byteorder), wordorder=getattr(Endian, self.control_data.power_pct_stpt.wordorder))
                    en_builder.add_16bit_uint(1)
                    en_payload = en_builder.build()
                    self.writeDataToRegisters(mbus.bytes_to_registers(encoded_payload),self.control_data.power_pct_stpt.batch_start_addr + self.control_data.power_pct_stpt.offset)
                    self.writeDataToRegisters(mbus.bytes_to_registers(en_payload),self.control_data.power_pct_stpt.en_start_addr + self.control_data.power_pct_stpt.en_offset)


    def decodeData(self, data_set: Dict[str, Any]):
        if 'read' not in data_set or not isinstance(data_set['read'], list):
            self.read_error = True
            return
        
        read_data = data_set['read']
        control_data_map = data_set.get('control', {})
        self.read_error = False


        for data_model_list_name in per_phase_data:
            list_of_data_models = getattr(self.measured_data, data_model_list_name, [])
            for dm_instance in list_of_data_models:
                if isinstance(dm_instance, dataModel) and dm_instance.model_present:
                    if dm_instance.block_num < len(read_data) and isinstance(read_data[dm_instance.block_num], list):
                        block_data_list = read_data[dm_instance.block_num]
                        if dm_instance.offset + dm_instance.size <= len(block_data_list):
                           dm_instance.data = block_data_list[dm_instance.offset : dm_instance.offset + dm_instance.size]
                           dm_instance.getData(read_data)
                        else: self.read_error = True
                    else: self.read_error = True

        if self.err_registers and hasattr(self.err_registers, 'errorDecode'): # Check if err_registers is initialized
            self.err_registers.errorDecode(read_data, self.device_id)

        # Iterate agg_data and also include today_energy if it's a defined attribute
        params_to_decode = agg_data[:] # Make a copy
        if hasattr(self.measured_data, "today_energy") and "today_energy" not in params_to_decode:
            params_to_decode.append("today_energy")


        for attr_name in params_to_decode:
            if not hasattr(self.measured_data, attr_name): continue

            dm_instance = getattr(self.measured_data, attr_name, None)
            if isinstance(dm_instance, dataModel) and dm_instance.model_present:
                if dm_instance.block_num < len(read_data) and isinstance(read_data[dm_instance.block_num], list):
                    block_data_list = read_data[dm_instance.block_num]
                    if dm_instance.offset + dm_instance.size <= len(block_data_list):
                        dm_instance.data = block_data_list[dm_instance.offset : dm_instance.offset + dm_instance.size]
                        dm_instance.getData(read_data)
                    else: self.read_error = True
                else: self.read_error = True
        
        if isinstance(control_data_map, dict):
            if self.control_data.poweer_lt.model_present:
                self.control_data.poweer_lt.getFactors(control_data_map)
            if self.control_data.power_pct_stpt.model_present:
                self.control_data.power_pct_stpt.getFactors(control_data_map)


    def writeDataToRegisters(self, data: List[int], address: int):
        if mbus and (self.comm_type == commType.modbus_rtu or self.comm_type == commType.modbus_tcp):
            mbus.writeModbusData(self, address, data)
    
    def writeDataToCtrlRegisters(self, data_to_ctrl: dict):
        pass


device_list: List[systemDevice] = []

class operatingDetails:
    system_operating_mode: Optional[systemOperatingModes] = None
    controlFunc: Any = None
    system_curtail_state: float = 0.0
    full_pv_curtail: float = 2.0
    agg_pv_rated: float = 0.0
    agg_batt_rated: float = 0.0
    aggDG: float = 0.0
    dg_lim: float = 0.0
    ref: float = 0.0
    scs_min: float = 0.0
    scs_max: float = 1.0
    aggPV: float = 0.0
    aggBatt: float = 0.0
    aggGrid: float = 0.0
    aggLoad: float = 0.0
    aggEV: float = 0.0
    load: float = 0.0
    Ki: float = default_Ki
    Kp: float = default_Kp
    Ts: float = float(default_Ts)
    err: float = 0.0
    storage_stpt: float = 0.0
    pv_stpt: float = 100.0
    safety_control_mode: int = 0
    io_output_data: Any = None
    mode_src : modeSrc = modeSrc.no_src

    def controlFuncConstPower(self):
        if self.agg_batt_rated != 0:
            self.storage_stpt = (100 * (self.load - self.aggPV - self.ref) / self.agg_batt_rated)
        else:
            self.storage_stpt = 0

    def controlPVChargeOnly(self):
        if self.agg_batt_rated != 0:
            self.storage_stpt = (100 * (-self.aggPV) / self.agg_batt_rated)
        else:
            self.storage_stpt = 0


    def controlFuncFullBackup(self):
        self.storage_stpt = -100

    def controlFuncFullExport(self):
        self.storage_stpt = 100

    def controlFuncGenLimit(self):
        self.pv_stpt = self.ref

    def controlFuncNone(self):
        self.storage_stpt = 0
        self.pv_stpt = 100

    def daily_peak_th_base_func(self):
        self.storage_stpt = min(self.agg_batt_rated,abs(self.ref - self.aggGrid)) * (2*(self.aggGrid > self.ref) - 1)

    def export_limit_func(self):
        self.pv_stpt = max(min(self.aggLoad - self.ref - self.aggBatt,self.agg_pv_rated),0)

    def dg_pv_sync_func(self):
        self.pv_stpt = min(self.agg_pv_rated,self.aggPV - (self.dg_lim - self.aggDG))

    def export_lim_export_priority_func(self):
        self.storage_stpt = min(0,self.aggBatt + min(0,self.ref+self.aggGrid))

    def safety_control_func(self):
        try:
            from io_master import iomasterapi as io
            if self.safety_control_mode == 0:
                io.ioDevice.write_digital_outputs(0)
            elif self.safety_control_mode == 1:
                io.ioDevice.write_digital_outputs(1, self.io_output_data)
        except ImportError:
            logging.error("io_master.iomasterapi not available for safety_control_func")


def setParameter(data_json: Dict[str, Any]):
    global device_list
    if "mode" in data_json:
        mode_val = data_json["mode"]
        ref_val = float(data_json.get("op_details", {}).get("ref", 0.0)) if isinstance(data_json.get("op_details"), dict) else 0.0
        updateOperatingMode(mode_val, ref_val)


    if "param" in data_json and "device_id" in data_json:
        if data_json['param'] == "active_power":
            try:
                device_id_to_control = int(data_json['device_id'])
                for device_instance in device_list:
                    if device_instance.device_id == device_id_to_control:
                        device_instance.encodeWrite(data_json)
                        break
            except ValueError:
                 logging.error(f"Invalid device_id for active_power: {data_json['device_id']}")


    if "device_state" in data_json and "device_id" in data_json:
        try:
            device_id_to_control = int(data_json['device_id'])
            for device_instance in device_list:
                if device_instance.device_id == device_id_to_control:
                    address = device_instance.control_data.device_state.batch_start_addr + device_instance.control_data.device_state.offset
                    data_to_ctrl:dict = {
                        "address": address,
                        "format" : device_instance.control_data.device_state.decoderFunc,
                        "value" : data_json["device_state"],
                        "wo" : device_instance.control_data.device_state.wordorder,
                        "bo": device_instance.control_data.device_state.byteorder
                    }
                    device_instance.writeDataToCtrlRegisters(data_to_ctrl)
                    break
        except ValueError:
            logging.error(f"Invalid device_id for device_state: {data_json['device_id']}")


def updateOperatingMode(mode_str: str, ref: float=0):
    logging.info(f"Attempting to update operating mode to {mode_str} with ref {ref}")
    
    resolved_mode_str = mode_str
    if mode_str in operatingMode_l2e:
        system_operating_details.system_operating_mode = operatingMode_l2e[mode_str]
    elif hasattr(systemOperatingModes, mode_str):
        system_operating_details.system_operating_mode = getattr(systemOperatingModes, mode_str)
    else:
        logging.error(f"Unknown operating mode string: {mode_str}")
        system_operating_details.system_operating_mode = systemOperatingModes.none
        resolved_mode_str = "none"

    system_operating_details.ref = ref
    control_func_name = resolved_mode_str + "_func"

    special_case_map = {
        "net_zero": "controlFuncConstPower",
        "pv_charge_only": "controlPVChargeOnly",
        "max_export": "controlFuncFullExport",
        "power_backup": "controlFuncFullBackup",
        "gen_limit": "controlFuncGenLimit",
        "none": "controlFuncNone",
        "safety_control_mode": "safety_control_func"
    }

    if resolved_mode_str in special_case_map:
        func_name_to_get = special_case_map[resolved_mode_str]
        if hasattr(system_operating_details, func_name_to_get):
            system_operating_details.controlFunc = getattr(system_operating_details, func_name_to_get)
        else:
            logging.error(f"Mapped control function {func_name_to_get} not found.")
            system_operating_details.controlFunc = system_operating_details.controlFuncNone
    elif hasattr(system_operating_details, control_func_name):
        system_operating_details.controlFunc = getattr(system_operating_details, control_func_name)
    else:
        logging.warning(f"No specific control function found for mode '{resolved_mode_str}' (tried {control_func_name}). Defaulting to None function.")
        system_operating_details.controlFunc = system_operating_details.controlFuncNone


    if resolved_mode_str == "net_zero":
        system_operating_details.scs_min = 0
        system_operating_details.scs_max = 1
    elif resolved_mode_str == "pv_charge_only":
        system_operating_details.scs_min = 0.5
        system_operating_details.scs_max = 1
    elif resolved_mode_str == "max_export":
        system_operating_details.scs_max = 0
        system_operating_details.scs_min = 0
    elif resolved_mode_str == "power_backup":
        system_operating_details.scs_max = 1
        system_operating_details.scs_min = 1

    current_func_name = system_operating_details.controlFunc.__name__ if system_operating_details.controlFunc else 'None'
    logging.info(f"{time.time()}: Mode changed to: {system_operating_details.system_operating_mode} ({resolved_mode_str}), Ref: {ref}, ControlFunc: {current_func_name}")


def batteryCurveFunc() -> float:
    if system_operating_details.system_curtail_state < 1:
        return 100.0 - 200.0 * system_operating_details.system_curtail_state
    else:
        return -100.0


def PVCurveFunc() -> float:
    if system_operating_details.system_curtail_state < 1:
        return 100.0
    else:
        denominator = system_operating_details.full_pv_curtail - 1.0
        if denominator == 0: return 0.0
        return (100.0 * (system_operating_details.full_pv_curtail - system_operating_details.system_curtail_state) / denominator)

def SetController(Kp: float,Ki: float,Ts: float):
    system_operating_details.Kp = Kp
    system_operating_details.Ki = Ki
    system_operating_details.Ts = Ts


def getAgg(device_type_to_agg: deviceType) -> tuple[float, float]:
    tmp_power_sum = 0.0
    agg_rated_power_sum = 0.0
    for device in device_list:
        if device.device_type == device_type_to_agg:
            total_power_attr = device.measured_data.total_power
            if total_power_attr is not None and total_power_attr.model_present:
                tmp_power_sum += total_power_attr.value
            agg_rated_power_sum += device.rated_power
    return tmp_power_sum, agg_rated_power_sum


def curtailStateToStpt():
    for device in device_list:
        if device.stptCurve is not None:
            setpoint_value = device.stptCurve()
            if device.rated_power != 0:
                absolute_power_target = setpoint_value * device.rated_power / 100.0
                data_msg = {"param": "active_power", "value": str(absolute_power_target), "device_id": str(device.device_id)}
                device.encodeWrite(data_msg)


def setModeSrc(src : str):
    if src == "schedule":
        system_operating_details.mode_src  = modeSrc.from_schedule
    elif src == "direct":
        system_operating_details.mode_src = modeSrc.direct_comm


def processMQTTMessage(message : str):
    logging.info(f"Processing MQTT message: {message}")
    if message == "start":
        if main: asyncio.run(main())
        return

    try:
        control_json = json.loads(message)
        setParameter(control_json)
        
        with open('control/control.json','w') as control_file:
            json.dump(control_json, control_file)
            
    except json.JSONDecodeError:
        logging.error(f"MQTT message is not a valid JSON: {message}")
    except Exception as e:
        logging.error(f"Error processing MQTT message '{message}': {e}")


def getActiveControlMode():
    if system_operating_details.aggDG > 0 and system_operating_details.dg_lim > 0 :
        updateOperatingMode("dg_pv_sync", system_operating_details.dg_lim)
    else:
        try:
            with open('control/control.json', 'r') as control_file:
                control_json = json.load(control_file)
                mode = control_json.get("mode")
                if mode:
                    ref = float(control_json.get("op_details", {}).get("ref", 0.0)) if isinstance(control_json.get("op_details"), dict) else 0.0
                    updateOperatingMode(mode, ref)
                else:
                    updateOperatingMode("none", 0.0)
        except FileNotFoundError:
            logging.info("control/control.json not found. Setting mode to none.")
            updateOperatingMode("none", 0.0)
        except json.JSONDecodeError:
            logging.error("Error decoding control/control.json. Setting mode to none.")
            updateOperatingMode("none", 0.0)
        except Exception as e:
            logging.error(f"Unexpected error in getActiveControlMode: {e}. Setting mode to none.")
            updateOperatingMode("none", 0.0)


def getAllData() -> Dict[str, Dict[str, Any]]:
    output_payload: Dict[str, Dict[str, Any]] = {}
    
    for device in device_list:
        device_id_str = str(device.device_id)
        current_device_data: Dict[str, Any] = {}
        
        device_type_str = deviceType_e2s.get(device.device_type, "unknown")
        current_device_data["type"] = str(device.num_phases) + "ph_" + device_type_str

        for param_list_name in per_phase_data:
            list_of_data_models = getattr(device.measured_data, param_list_name, [])
            for i, dm_instance in enumerate(list_of_data_models):
                if isinstance(dm_instance, dataModel) and dm_instance.model_present:
                    key_name = "L" + str(i + 1) + "_" + data_decode.get(param_list_name, param_list_name.lower())
                    current_device_data[key_name] = dm_instance.value

        parameters_to_check = agg_data[:]
        if hasattr(device.measured_data, "today_energy") and "today_energy" not in parameters_to_check :
             parameters_to_check.append("today_energy")


        for param_name in parameters_to_check:
            if not hasattr(device.measured_data, param_name):
                continue

            dm_instance = getattr(device.measured_data, param_name, None)
            
            if dm_instance is not None and isinstance(dm_instance, dataModel) and dm_instance.model_present:
                value_to_check = dm_instance.value
                
                if value_to_check is None:
                    continue 
                if isinstance(value_to_check, list) and value_to_check == [None, None]:
                    continue 
                
                current_device_data[param_name] = value_to_check
        
        if len(current_device_data.keys() - {'type'}) > 0:
            output_payload[device_id_str] = current_device_data
            
    return output_payload


def getLivePower() -> Dict[str, Optional[float]]:
    data: Dict[str, Optional[float]] = {}
    for device in device_list:
        device_id_str = str(device.device_id)
        total_power_dm = device.measured_data.total_power
        if total_power_dm is not None and isinstance(total_power_dm, dataModel) and total_power_dm.model_present:
            data[device_id_str] = total_power_dm.value
        else:
            data[device_id_str] = None
    return data


def getAggDG():
    system_operating_details.aggDG = 0.0
    for device in device_list:
        if device.device_type == deviceType.meter and device.connected_to == str(deviceType.DG.value):
            total_power_dm = device.measured_data.total_power
            if total_power_dm is not None and total_power_dm.model_present:
                system_operating_details.aggDG += total_power_dm.value

def getAggGrid():
    system_operating_details.aggGrid = 0.0
    for device in device_list:
        if device.device_type == deviceType.meter and device.connected_to == str(deviceType.grid.value):
            total_power_dm = device.measured_data.total_power
            if total_power_dm is not None and total_power_dm.model_present:
                system_operating_details.aggGrid += total_power_dm.value


def runSysControlLoop():
    getActiveControlMode()

    system_operating_details.aggPV, system_operating_details.agg_pv_rated = getAgg(deviceType.solar)
    system_operating_details.aggBatt, system_operating_details.agg_batt_rated = getAgg(deviceType.battery)
    system_operating_details.aggEV, _ = getAgg(deviceType.EV)
    
    system_operating_details.load = 0.0
    for device in device_list:
        if device.device_type == deviceType.meter and \
           device.connected_to != str(deviceType.DG.value) and \
           device.connected_to != str(deviceType.grid.value):
            if device.measured_data.total_power and device.measured_data.total_power.model_present:
                system_operating_details.load += device.measured_data.total_power.value
    
    getAggDG()
    getAggGrid() 

    if system_operating_details.controlFunc is not None:
        system_operating_details.controlFunc()
        for device in device_list:
            if device.device_type == deviceType.battery:
                power_val = 0.0
                if device.rated_power != 0:
                    power_val = system_operating_details.storage_stpt * device.rated_power / 100.0
                
                data_msg = {"param" : "active_power", "value": str(power_val), "device_id": str(device.device_id)}
                device.encodeWrite(data_msg)

            if device.device_type == deviceType.solar:
                power_val = 0.0
                if device.rated_power != 0:
                     power_val = system_operating_details.pv_stpt * device.rated_power / 100.0

                data_msg = {"param" : "active_power", "value": str(power_val), "device_id": str(device.device_id)}
                device.encodeWrite(data_msg)

def getDeviceType(device_id_to_find: int) -> Optional[deviceType]:
    for device in device_list:
        if(device.device_id == device_id_to_find):
            return device.device_type
    return None

system_operating_details = operatingDetails()
