import time
import board
import busio

import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)

ads1 = ADS.ADS1115(i2c, address=0x48)
ads2 = ADS.ADS1115(i2c, address=0x49)
ads1.gain = 1
ads2.gain = 1


chan0_ads1 = AnalogIn(ads1, ADS.P0)
chan0_ads2 = AnalogIn(ads2, ADS.P0)


try:
    while True:
        print(f"0x48 : {chan0_ads1.value} , {chan0_ads1.voltage} V")
        time.sleep(1)
        print(f"0x49 : {chan0_ads2.value} , {chan0_ads2.voltage} V")
        time.sleep(1)

except KeyboardInterrupt:
    print("Stopped by user")

