
import os
import json
import time
def connect(ssid,password):
    #wifi_cfgfile = open("wpa_supplicant.conf",'a')
    #network='network={\n\tssid="' + str(ssid) +'"\n\tpsk="'+ str(password)+'"\n\tkey_mgmt=WPA-PSK\n}'
    #wifi_cfgfile.write(network)
    print("connect to : ",ssid,password)
    wifi_data = {'ssid':ssid,'password':password}
    os.system("sudo raspi-config nonint do_wifi_ssid_passphrase " + " " +str(ssid) + " " + str(password))
    with open("wifi_cfg_file.json", mode="w", encoding="utf-8") as write_file:
        json.dump(wifi_data, write_file)
    os.system("sudo raspi-config nonint do_wifi_ssid_passphrase " + " " +str(ssid) + " " + str(password))
    time.sleep(1)
    os.system("reboot")