import serial

ser = serial.Serial('/dev/ttyUSB0', 115200 , timeout=2) #, write_timeout=2) #blocking time out 2s
try:
  ser.open()
except serial.SerialException as err:
  #print err
  #print "closing port"
  try:
    ser.close()
    ser.open()
  except serial.SerialException as er2:
   print "failed twice " + er2
print "Opening serial port"
