import RPi.GPIO as GPIO
import time
import subprocess
import sys

def install(package):
    subprocess.call([sys.executable, "-m", "pip3", "install", package])
    
try:
    import Adafruit_DHT
except:
    install('Adafruit-DHT==1.3.4')

#import logging

#logging.basicConfig(format='%(levelname)s-%(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG,filename='/App/gpio.log')

# Set GPIO mode: GPIO.BCM or GPIO.BOARD
GPIO.setmode(GPIO.BCM) 

# GPIO pins list based on GPIO.BOARD
# gpioList1 = [17,18]
# gpioList2 = [14,15]

# Set mode for each gpio pin
GPIO.setup(17, GPIO.OUT, initial= GPIO.LOW)
GPIO.setup(18, GPIO.OUT, initial= GPIO.HIGH)

#GPIO.setup(gpioList2, GPIO.IN)

def set_status(pin,status):
    GPIO.output(pin, status)
    return GPIO.input(pin)

def get_status(pin,status):
    return GPIO.input(pin)

def get_temp(pin):
    try:
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, pin)
    except ImportError as e:
        print(e)
        return 0 
    return temperature

def get_humid(pin):
    try:
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, pin)
    except ImportError as e:
        print(e)
        return 0
    return humidity


