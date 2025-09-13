import os
import json

if(os.path.isfile("wifi_cfg_file.json")):
        with open("wifi_cfg_file.json") as wifi_file:
            wifi_cfg = json.load(wifi_file)
            ssid = wifi_cfg['ssid']
            password = wifi_cfg['password']
            os.system("sudo raspi-config nonint do_wifi_ssid_passphrase " + " " +str(ssid) + " " + str(password))
        
else:
      pass
      #os.system("sudo nmcli device wifi hotspot ssid conntrolEDconfig password connectx")