import json

from flask import Flask, request, flash, url_for, redirect, \
     render_template, jsonify, Response, send_file

from control import set_status, get_temp, get_humid, get_hour 
import RPi.GPIO as GPIO

#from camera_pi import Camera
from camera_pi import save_image
from celery import Celery
from picamera import PiCamera

import requests

from datetime import timedelta, datetime
from celery.schedules import crontab

#camera = PiCamera()

app = Flask(__name__)
content_type_json = {'Content-Type': 'text/css; charset=utf-8'}
app.config['DEBUG'] = False
app.config['SECRET_KEY'] = 'super-secret'
app.config['SECURITY_PASSWORD_SALT'] = 'salt'
 
water_pin = 17
COB_pin = 18
temp_hum_pin = 15
vent_pin = 14

lastfile = "static/1.jpg"

server_url = "https://hoog-cluster.herokuapp.com/api/"

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_TIMEZONE'] = 'UTC'
app.config['CELERYBEAT_SCHEDULE'] = {
    'water-every-morning': {
        'task': 'tasks.turn_water_on',
        'schedule': crontab(hour=get_hour(water_pin, True), minute=0)
    },
    'water-later': {
        'task': 'tasks.turn_water_off',
        'schedule': crontab(hour=get_hour(water_pin, False), minute=1)
    },
    'COB-every-morning': {
        'task': 'tasks.turn_COB_on',
        'schedule': crontab(hour=get_hour(COB_pin, True), minute=0)
    },
    'COB-later': {
        'task': 'tasks.turn_COB_off',
        'schedule': crontab(hour=get_hour(COB_pin, False), minute=0)
    },
    'vent-every-morning': {
        'task': 'tasks.turn_vent_on',
        'schedule': crontab(hour=get_hour(vent_pin, True), minute=0)
    },
    'vent-later': {
        'task': 'tasks.turn_vent_off',
        'schedule': crontab(hour=get_hour(vent_pin, False), minute=0)
    },
    'measurements': {
        'task': 'tasks.measurements',
        'schedule': crontab(hour='*', minute=0)
    }
}

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task(name='tasks.turn_water_on')
def turn_water_on():
    print('Water (pin 17) turned on')
    return set_status(water_pin, GPIO.HIGH)

@celery.task(name='tasks.turn_water_off')
def turn_water_off():
    print('Water (pin 17) turned off')
    return set_status(water_pin,GPIO.LOW)

@celery.task(name='tasks.turn_COB_on')
def turn_COB_on():
    print('COB (pin 18) turned on')
    return set_status(COB_pin, GPIO.HIGH)

@celery.task(name='tasks.turn_COB_off')
def turn_COB_off():
    print('COB (pin 17) turned off')
    return set_status(COB_pin,GPIO.LOW)

@celery.task(name='tasks.turn_vent_on')
def turn_vent_on():
    print('vent (pin 14) turned on')
    return set_status(vent_pin, GPIO.HIGH)

@celery.task(name='tasks.turn_vent_off')
def turn_vent_off():
    print('vent (pin 14) turned off')
    return set_status(vent_pin,GPIO.LOW)

@celery.task(name='tasks.measurements')
def measurements():
    print('measurements taken')
    r = requests.post(server_url , data = {'key':'value'})
    return 124


@app.route('/')
def home():
    return render_template('dashboard.html')

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/water_status')
def get_water_status():
    return jsonify(
        status=GPIO.input(water_pin)
    )

@app.route('/water_on')
def get_water_on():
    turn_water_on()
    return jsonify(
        status=GPIO.input(water_pin)
    )

@app.route('/water_off')
def get_water_off():
    turn_water_off()
    return jsonify(
        status=GPIO.input(water_pin)
    )

@app.route('/COB_status')
def get_COB_status():
    return jsonify(
        status=GPIO.input(COB_pin)
    )

@app.route('/COB_on')
def get_COB_on():
    turn_COB_on()
    return jsonify(
        status=GPIO.input(COB_pin)
    )

@app.route('/COB_off')
def get_COB_off():
    turn_COB_off()
    return jsonify(
        status=GPIO.input(COB_pin)
    )

@app.route('/vent_off')
def get_vent_off():
    turn_vent_off()
    return jsonify(
        status=GPIO.input(vent_pin)
    )

@app.route('/vent_on')
def get_vent_on():
    turn_vent_on()
    return jsonify(
        status=GPIO.input(vent_pin)
    )

@app.route('/measurements')
def get_measurements():
    return jsonify(
        vent=GPIO.input(vent_pin),
        light=GPIO.input(COB_pin),
        water=GPIO.input(water_pin),

    )  

@app.route('/schedule', methods = ['POST', 'GET'])
def post_schedule():
    if request.method == 'POST':
        with open('schedule.json', 'w') as outfile:
            json.dump(request.json, outfile)
        
        return jsonify(success="true")
    else:
        with open('schedule.json') as f:
            data = json.load(f)
        return jsonify(data)

@app.route('/show')
def show_all():
    with open('schedule.json') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/temperature')
def get_temperature():
    temperature = get_temp(temp_hum_pin)
    return jsonify(
        temperature=temperature
    )

@app.route('/humidity')
def get_humidity():
    humidity = get_humid(temp_hum_pin)
    return jsonify(
        humidity=humidity
    )

# @app.route('/video_feed')
# def video_feed():
#     return Response(gen(Camera()),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/snapshot')
def snapshot():
    return send_file(save_image())

@app.route("/snapshot2")
def getImage():
     camera.capture(lastfile)
     camera.close()
     return send_file(lastfile)

# @app.route('/create_user')
# def create_user():
#     try:
#         init_db()
#         user_datastore.create_user(email='admin', password='password')
#         db_session.commit()
#         return 'Success'
#     except:
#         db_session.rollback()
#         return 'Failed'

if __name__ == '__main__':
    try:
        # try the production run
        app.run(host='0.0.0.0', port=80)
    except PermissionError:
        # we're probably on the developer's machine
        app.run(host='0.0.0.0', port=5000, debug=False)
        
