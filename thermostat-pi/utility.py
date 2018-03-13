
# handles logging and provides common functions
from datetime import datetime
import time
import logging
import logging.handlers
import json

try:
	import RPi.GPIO as GPIO
except ImportError:
	pass

PREFSFILE = "./prefs.json"
LOGFILE = "./thermostat.log"

BACKLIGHT_PIN = 18
RELAY_PIN = 4


# helper functions

def savePrefs(prefs):
	print("Saving preferences: " + str(prefs))
	with open(PREFSFILE, 'w') as fp:
		json.dump(prefs, fp, sort_keys=True, indent=4)

def loadPrefs():
	try:
		with open(PREFSFILE, 'r') as fp:
			return json.load(fp)
	except IOError:
		return None

def initializeGPIO():
	global backlight_pwm

	try:
		GPIO.setmode(GPIO.BCM)

		GPIO.setup(RELAY_PIN, GPIO.OUT)
		GPIO.output(RELAY_PIN, False)
		
		GPIO.setup(BACKLIGHT_PIN, GPIO.OUT)
		GPIO.output(BACKLIGHT_PIN, True)
		backlight_pwm = GPIO.PWM(BACKLIGHT_PIN, 1000)
		backlight_pwm.start(100)
	except NameError:
		pass

def setBacklight(value):
	global backlight_pwm

	try:
		backlight_pwm.ChangeDutyCycle(value)
	except NameError:
		pass

def setRelay(value):
	try:
		GPIO.output(RELAY_PIN, value)
	except NameError:
		pass

class MockThermostat:
	def __init__(self):
		# configurable parameters
		self.cycleDuration = 300 # this should be 300 seconds for safety
		self.failsafe = False

		# internal status
		self.currentTemp = 18.5
		self.lastTempUpdate = time.time()
		self.lastCycle = time.time() - self.cycleDuration / 3 # allows it to start up immediately
		self.heating = True

	def status(self):
		return "(Test Status)"

	def updateTemp(self, t):
		print("Would update temp = " + str(t))

	def evaluate(self):
		print('would evaluate themostat')



def convert(units, t):
	if units == 'F':
		return t * 9.0 / 5.0 + 32.0
	else:
		return t

def tempstr(t):	
	return u"%2.1f" % t

def timestamp():
	 return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def formatDuration(dt):
	dt = int(dt)
	if dt > 60*60:
		hours = int(dt/3600)
		minutes = int(dt / 60) - hours*60
		seconds = dt - minutes * 60 - hours * 3600
		return str(hours) + 'h ' + str(minutes) + 'm ' + str(seconds) + 's'
	elif dt > 60:
		minutes = int(dt / 60)
		seconds = dt - minutes * 60
		return str(minutes) + 'm ' + str(seconds) + 's' 
	else:
		return str(dt) + 's' 

# create log
log = logging.getLogger('')
log.setLevel(logging.DEBUG)

format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                              '%Y-%m-%d %H:%M:%S')

ch = logging.StreamHandler()
ch.setFormatter(format)
log.addHandler(ch)


fh = logging.handlers.RotatingFileHandler(LOGFILE, maxBytes=1048576, backupCount=10)
fh.setLevel(logging.INFO)
fh.setFormatter(format)
log.addHandler(fh)

initializeGPIO()

