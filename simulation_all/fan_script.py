import os
import time
import RPi.GPIO as GPIO

# ======= CONFIGURATION =======
FAN_PIN = 17               # GPIO pin (BCM numbering)
FAN_ON_TEMP = 45.0         # Fan ON threshold (°C)
FAN_OFF_TEMP = 40.0        # Fan OFF threshold (°C)
CHECK_INTERVAL = 10         # Check every second
MIN_FAN_RUN_TIME = 30      # Fan must run at least this long before turning off
# =============================

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(FAN_PIN, GPIO.OUT)
GPIO.output(FAN_PIN, GPIO.LOW)
fan_on = False
fan_start_time = None

def get_cpu_temp():
    """Read CPU temperature using vcgencmd."""
    res = os.popen('vcgencmd measure_temp').readline()
    return float(res.replace("temp=", "").replace("'C\n", ""))

try:
    print("🌡️ Fan control script started.")
    while True:
        temp = get_cpu_temp()
        current_time = time.time()

        # Turn fan ON
        if temp > FAN_ON_TEMP and not fan_on:
            GPIO.output(FAN_PIN, GPIO.HIGH)
            fan_on = True
            fan_start_time = current_time
            print(f"Temp: {temp}°C -> 🌀 Fan ON")

        # Turn fan OFF only if minimum run time is satisfied
        elif temp < FAN_OFF_TEMP and fan_on:
            if current_time - fan_start_time >= MIN_FAN_RUN_TIME:
                GPIO.output(FAN_PIN, GPIO.LOW)
                fan_on = False
                print(f"Temp: {temp}°C -> 🛑 Fan OFF")
            else:
                print(f"Temp: {temp}°C -> Fan running (waiting {int(MIN_FAN_RUN_TIME - (current_time - fan_start_time))}s)")

        else:
            print(f"Temp: {temp}°C -> {'Fan ON' if fan_on else 'Fan OFF'}")

        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    print("\n🧹 Cleaning up GPIO and exiting...")
    GPIO.output(FAN_PIN, GPIO.LOW)
    GPIO.cleanup()
