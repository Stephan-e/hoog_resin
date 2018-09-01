import json

from flask import Flask, render_template
from control import set_status
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
    return set_status(17, GPIO.HIGH)

@celery.task(name='tasks.turn_water_off')
def turn_water_off():
    print('Water (pin 17) turned off')
    return set_status(17,GPIO.LOW)

@celery.task(name='tasks.turn_COB_on')
def turn_COB_on():
    print('COB (pin 18) turned on')
    return set_status(18, GPIO.HIGH)

@celery.task(name='tasks.turn_COB_off')
def turn_COB_off():
    print('COB (pin 17) turned off')
    return set_status(18,GPIO.LOW)


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

# @app.route('/')
# def hello_world():
#     msg = 'Device: <a href="/water_on">Turn water on</a> or <a href="/water_off">Turn water off</a>. Device: <a href="/COB_on">Turn COB on</a> or <a href="/COB_off">Turn COB off</a>.'
#     return msg
@app.route('/water_status')
def get_water_status():
    status = GPIO.input(18)
    return '{{status}}'

@app.route('/water_on')
def get_water_on():
    turn_water_on.delay()
    return 'Turning water on! <a href="/">back</a>'

@app.route('/water_off')
def get_water_off():
    turn_water_off.delay()
    return 'Turning water off! <a href="/">back</a>'

@app.route('/COB_status')
def get_COB_status():
    status = GPIO.input(17)
    return status

@app.route('/COB_on')
def get_COB_on():
    turn_COB_on.delay()
    return 'Turning COB on! <a href="/">back</a>'

@app.route('/COB_off')
def get_COB_off():
    turn_COB_off.delay()
    return 'Turning COB off! <a href="/">back</a>'

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
        