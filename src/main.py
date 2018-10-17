import json

from flask import Flask, render_template, jsonify, Response
from control import set_status, get_temp, get_humid 
import RPi.GPIO as GPIO
from flask_security import Security, login_required, \
     SQLAlchemySessionUserDatastore
from database import db_session, init_db
from models import User, Role
from camera import Camera


app = Flask(__name__)
content_type_json = {'Content-Type': 'text/css; charset=utf-8'}
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'super-secret'
app.config['SECURITY_PASSWORD_SALT'] = 'salt'

# Setup Flask-Security
user_datastore = SQLAlchemySessionUserDatastore(db_session,
                                                User, Role)
security = Security(app, user_datastore)

water_pin = 17
COB_pin = 18
temp_hum_pin = 15
vent_pin = 14

# Celery conf
from celery import Celery
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
#app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.config['CELERY_TIMEZONE'] = 'UTC'

# execute task at certain intervals
from datetime import timedelta
from celery.schedules import crontab
app.config['CELERYBEAT_SCHEDULE'] = {
    'water-every-morning': {
        'task': 'tasks.turn_water_on',
        'schedule': crontab(hour=get_hour().water_on, minute=0)
    },
    'water-later': {
        'task': 'tasks.turn_water_off',
        'schedule': crontab(hour=get_hour().water_off, minute=1)
    },
    'COB-every-morning': {
        'task': 'tasks.turn_COB_on',
        'schedule': crontab(hour=get_hour().COB_on, minute=0)
    },
    'COB-later': {
        'task': 'tasks.turn_COB_off',
        'schedule': crontab(hour=get_hour().COB_off, minute=0)
    }
    'vent-every-morning': {
        'task': 'tasks.turn_vent_on',
        'schedule': crontab(hour=get_hour().vent_on, minute=0)
    },
    'vent-later': {
        'task': 'tasks.turn_vent_off',
        'schedule': crontab(hour=get_hour().vent_off, minute=0)
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


# Create a user to test with
@app.before_first_request
def initialise_db():
    init_db()
    db_session.commit()


# Routes for manual controls
############################
@app.route('/')
@login_required
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

@app.route('/schedule', methods = ['POST'])
def post_schedule():
    if request.method == 'POST':
       return jsonify(request.form)
    # data = request.form

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

@app.route('/video_feed')
def video_feed():
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/create_user')
def create_user():
    try:
        init_db()
        user_datastore.create_user(email='admin', password='password')
        db_session.commit()
        return 'Success'
    except:
        db_session.rollback()
        return 'Failed'

if __name__ == '__main__':
    try:
        # try the production run
        app.run(host='0.0.0.0', port=80)
    except PermissionError:
        # we're probably on the developer's machine
        app.run(host='0.0.0.0', port=5000, debug=True)
        