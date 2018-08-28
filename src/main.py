import json

from flask import Flask
from control import set_on, set_off
import RPi.GPIO as GPIO


app = Flask(__name__)
content_type_json = {'Content-Type': 'text/css; charset=utf-8'}

# Celery conf
from celery import Celery
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
#app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.config['CELERY_TIMEZONE'] = 'UTC'

# execute task at certain intervals
from datetime import timedelta
from celery.schedules import crontab
app.config['CELERYBEAT_SCHEDULE'] = {
    'play-every-morning': {
        'task': 'tasks.turn_on',
        'schedule': crontab(hour=17, minute=20)
    },
    'pause-later': {
        'task': 'tasks.turn_off',
        'schedule': crontab(hour=17, minute=21)
    }
}

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task(name='tasks.turn_on')
def turn_on():
    print('pin 17 turned on')
    return set_on(17, GPIO.HIGH)

@celery.task(name='tasks.turn_off')
def turn_off():
    print('pin 17 turned off')
    return set_status(17,GPIO.LOW)

# Routes for manual controls
############################

@app.route('/')
def hello_world():
    msg = 'Device: <a href="/on">Turn on</a> or <a href="/off">Turn off</a>.'
    return msg

@app.route('/on')
def get_play():
    turn_on.delay()
    return 'Turning on! <a href="/">back</a>'

@app.route('/off')
def get_pause():
    turn_off.delay()
    return 'Turning off! <a href="/">back</a>'

if __name__ == '__main__':
    try:
        # try the production run
        app.run(host='0.0.0.0', port=80)
    except PermissionError:
        # we're probably on the developer's machine
        app.run(host='0.0.0.0', port=5000, debug=True)
