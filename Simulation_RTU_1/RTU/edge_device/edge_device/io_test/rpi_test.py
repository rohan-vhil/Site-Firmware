import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN)
GPIO.setup(27, GPIO.OUT, pull_up_down=GPIO.PUD_DOWN)

try:

    while True:
        button_state = GPIO.input(17)
        print("Button state is :", button_state)
        if GPIO.input(17) == GPIO.HIGH:
            GPIO.output(27, GPIO.HIGH)
            time.sleep(1)
        else:
            GPIO.output(27, GPIO.LOW)
            time.sleep(1)

except Exception as e:
    GPIO.output(27, GPIO.LOW)
    GPIO.cleanup()

