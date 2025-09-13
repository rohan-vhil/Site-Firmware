import os
import sqlite3 as sqldb
import json
import sys

from datetime import datetime
import pytz

sys.path.insert(0, "../")
import time
from modbus_master import modbusmasterapi as mbus
from control import control_base as ctrl
import requests
import logging
import json
from threading import Lock
import enum
sys.path.insert(1, "../")
config_path = "/home/edge_device/edge_device/installer_cfg/"
path = config_path + "installer_cfg.json" 
import path_config
class reportType(enum.IntEnum):
    average=0
    all=1

    @classmethod
    def from_param(cls, obj):
        return int(obj)


def set_localdate():
    epoch_timestamp = int(time.time())
    timezone_str = 'Asia/Kolkata'

    utc_date = datetime.fromtimestamp(epoch_timestamp, tz=pytz.utc)

    local_timezone = pytz.timezone(timezone_str)
    local_date = utc_date.astimezone(local_timezone)

    return local_date.strftime('%Y-%m-%d')


class dataBank:
    data_queue = []
    avg_data :dict = {}
    report_url : str = ""
    report_period :int = 0
    report_type : reportType = reportType.average
    cnt = 0
    def __init__(self) -> None:
        pass

    def aggData(self,msg):
        #print(msg)
        self.data_queue.append(msg)
        pass

    def getAvg(self,device_id):
        self.avg_data[str(device_id)] = {}
        self.avg_data[str(device_id)] = {"local_date" : str(set_localdate())}
        device_data = [x.get(str(device_id)) for x in self.data_queue]
        #print(len(device_data))
        if(len(device_data) > 0):
            #print(device_data[0])
            for param in device_data[0]:
                if(param != "type"):
                    data = [x.get(param) for x in device_data]
                    if isinstance(data[0], (int, float)):
                        self.avg_data[str(device_id)][param] = round(sum(data)/len(data), 2)  #analog data also average
                    else:
                        self.avg_data[str(device_id)][param] = data  #latest data of digital inputs
                    
                else:
                    self.avg_data[str(device_id)]["type"] = device_data[0]["type"]
                pass
            
            



    def runDataLoop(self):
        while( not os.path.exists(path_config.path_cfg.base_path + "devices.json")):
            #print("no file")
            pass
        while(os.path.exists(path_config.path_cfg.base_path + "devices.json")):
            self.data_queue
            with open(path_config.path_cfg.base_path + "reports_handling/report_cfg.json") as report_cfg:
                report_config = json.load(report_cfg)
            self.report_url = report_config["report_url"] #+ str(ctrl.site_id)
            self.report_period = report_config["reporting_period"]
            self.report_type = getattr(reportType,report_config["report_type"])

            for device in ctrl.device_list:
                self.getAvg(device.device_id)
                pass
            


   
            self.data_queue = [] #clear the buffer
            self.avg_data["timestamp"] = int(time.time())
            response=None

            #write_msg = str(self.avg_data)
            #file = open("logs.log", "a")
            #file.write(write_msg + "\n")
            #file.close()

            try:
                #write data to json 
                #try to send entire json 
                #if fail, continue and ad data
                #uf send successfull, then delete json 
                response = requests.post(self.report_url,json=[self.avg_data],verify=False)
                print(self.report_url,(self.avg_data),response)
            except Exception as e:
                print(response)
                print(e)
             
            time.sleep(self.report_period)

        pass
        
        
data_handler : dataBank = None


def sendData(msg, url_ext):
    api_url_test = "http://127.0.0.1:5000/" + url_ext
    # print(api_url)
    fail_status = False
    #print("cloud status checked")
    try:
        # response = requests.post(api_url, json=msg, verify=False)
        # response.raise_for_status()
        response1 = requests.post(api_url_test, json=msg, verify=False)
        response1.raise_for_status()
        # logging.info(
        #     "message sent : " + str(response.status_code) + str(response.content)
        # )
        logging.info(
            "message sent : " + str(response1.status_code) + str(response1.content)
        )
        #print("message has been sent o the cloud")
    except Exception as e:
        fail_status = True
        #print("message sending failed cloud down")
        # print(d['cloud_status'])
        logging.warning("failed to send data " + str(e))
        response = None

    # response = requests.post(api_url, json=msg,verify=False)
    # fail_status = False

    return fail_status


def SendReports():
    while 1:
        with Lock():
            time_stamp = str(time.time())
            # api_url = "https://conntrol-os.io/api/data/solar"
            i = 0
            for device in ctrl.device_list:
                # i=i+1
                # print("new entry",i)
                devicetype = ["solar", "battery", "meter", "ev"]
                fail_status = False
                if(device.read_error):

                    message = {"data": [{"vppId": ctrl.vpp_id,"houseId": ctrl.site_id,"deviceId": device.device_id,"timestamp": time_stamp,"power": device.measured_data.P.value,"energy": device.measured_data.En.value,"ignore":device.read_error}]}
                else:
                    message = {"data": [{"vppId": ctrl.vpp_id,"houseId": ctrl.site_id,"deviceId": device.device_id,"timestamp": time_stamp,"power": device.measured_data.P.value,"energy": device.measured_data.En.value}]}
                fail_status = sendData(
                    msg=message, url_ext=devicetype[device.device_type]
                )
                #print(message)
                #print(devicetype[device.device_type])
                try:
                    with open("../energy.json", "w") as e:
                        temp = {}
                        temp["power"] = device.measured_data.P.value
                        temp["power"] = device.measured_data.En.value
                        # temp["energy"] = energy
                        json.dump(temp, e)
                except (FileNotFoundError, json.JSONDecodeError):
                    pass

                # print(message.json())
                write_msg = (
                    str(device.device_id)
                    + ","
                    + str(time_stamp)
                    + ","
                    + str(device.measured_data.P.value)
                    + ","
                    + str(device.measured_data.En.value)
                    + ","
                    + str(fail_status)
                    + ","
                    +str(devicetype[device.device_type])
                )
                file = open("logs.log", "a")
                file.write(write_msg + "\n")
                file.close()
                # print(os.path.getsize('logs.log'))
                if os.path.getsize("logs.log") > 10 * 1024 * 1024:
                    os.remove("logs.log")
                cmd = "INSERT INTO data VALUES "
                cmddel = (
                    "DELETE FROM data where timestamp=(SELECT MAX(timestamp) from data;"
                )
                cmd = (
                    cmd
                    + "("
                    + str(device.device_id)
                    + ","
                    + str(time_stamp)
                    + ","
                    + str(device.measured_data.P.value)
                    + ","
                    + str(device.measured_data.En.value)
                    + ","
                    + str(fail_status)
                    + ");"
                )
                # log = str(time_stamp)+","+str(device.measured_data.P.value) +","+ str(device.measured_data.En.value) +","+ str(fail_status)
                # logging.info(log)

                try:
                    con = sqldb.connect("system_data.db")
                    cur = con.cursor()
                    if os.path.getsize("system_data.db") > 10 * 1024 * 1024:
                        cur.execute(cmddel)
                    con.commit()
                    cur.execute(cmd)
                    con.commit()
                except Exception as e:
                    logging.warning("error in storing data in db" + str(e))

                try:
                    cur.execute("SELECT * FROM data WHERE fail = True;")
                    unsent_data = cur.fetchall()
                    logging.debug(str(unsent_data))
                    for x in unsent_data:
                        cmd = "UPDATE data SET fail = "
                        cmd2 = " WHERE timestamp = "
                        msg = {
                            "data": [
                                {
                                    "vppId": ctrl.vpp_id,
                                    "houseId": ctrl.site_id,
                                    "deviceId": str(device.device_id),
                                    "timestamp": x[1],
                                    "power": x[2],
                                    "energy": x[3],
                                }
                            ]
                        }
                        fail_status = sendData(
                            msg, url_ext=devicetype[device.device_type]
                        )

                        cmd = cmd + str(fail_status) + cmd2 + str(x[1]) + ";"
                        cur.execute(cmd)
                        con.commit()

                except Exception as e:
                    logging.log("error storing unsent data" + str(e))

                con.close()
        time.sleep(10)
