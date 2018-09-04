import json

from flask import Flask, render_template, jsonify
from control import set_status, get_temp, get_humid 
import RPi.GPIO as GPIO
from flask_security import Security, login_required, \
     SQLAlchemySessionUserDatastore
from database import db_session, init_db
from models import User, Role



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
        'schedule': crontab(hour=10, minute=0)
    },
    'water-later': {
        'task': 'tasks.turn_water_off',
        'schedule': crontab(hour=10, minute=1)
    },
    'COB-every-morning': {
        'task': 'tasks.turn_COB_on',
        'schedule': crontab(hour=8, minute=0)
    },
    'COB-later': {
        'task': 'tasks.turn_COB_off',
        'schedule': crontab(hour=23, minute=0)
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
        