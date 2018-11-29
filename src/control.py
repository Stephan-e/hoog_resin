import RPi.GPIO as GPIO
import time
import subprocess
import sys, json
import time

def install(package):
    subprocess.call([sys.executable, "-m", "pip", "install", package])

try:
    import Adafruit_DHT
except:
    install('Adafruit-DHT==1.3.4')
    import Adafruit_DHT
 


#import logging

#logging.basicConfig(format='%(levelname)s-%(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG,filename='/App/gpio.log')

# Set GPIO mode: GPIO.BCM or GPIO.BOARD
GPIO.setmode(GPIO.BCM) 

# GPIO pins list based on GPIO.BOARD
# gpioList1 = [17,18]
# gpioList2 = [14,15]

# Set mode for each gpio pin
GPIO.setup(14, GPIO.OUT, initial= GPIO.HIGH)
GPIO.setup(17, GPIO.OUT, initial= GPIO.LOW)
GPIO.setup(18, GPIO.OUT, initial= GPIO.HIGH)

water_pin = 17
COB_pin = 18
temp_hum_pin = 15
vent_pin = 14

#GPIO.setup(gpioList2, GPIO.IN)


def measure(pin):
    return Adafruit_DHT.read(Adafruit_DHT.DHT22, pin)

def set_status(pin,status):
    GPIO.output(pin, status)
    return GPIO.input(pin)

def get_status(pin):
    status = GPIO.input(pin)
    if status == 1:
        return True
    elif status == 0: 
        return False

def get_temp(pin):
    timeout = time.time() + 1
    while True:
        humidity, temperature = measure(pin)
        if temperature is not None and temperature is not None or time.time() > timeout:
            break
        
    temp = round(temperature,2)
    return temp

def get_humid(pin):
    timeout = time.time() + 1  
    while True:
        humidity, temperature = measure(pin)
        if temperature is not None and temperature is not None or time.time() > timeout:
            break

    hum = round(humidity,2)
    return hum     

def get_hour(pin, state):

    with open('schedule.json') as f:
        data = json.load(f)

    if pin == water_pin and state == True:
        return data['water_hour_on']
    elif pin == water_pin and state == False:
        return data['water_hour_off']
    
    elif pin == COB_pin and state == True:
        return data['COB_hour_on']
    elif pin == COB_pin and state == False:
        return data['COB_hour_off']

    elif pin == vent_pin and state == True:
        return data['vent_hour_on']
    elif pin == vent_pin and state == False:
        return data['vent_hour_off']

    else:
        return 0
    



