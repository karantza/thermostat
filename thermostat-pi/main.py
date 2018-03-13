import threading
from utility import *
import RPi.GPIO as GPIO

preferences = loadPrefs() or {
	'units': 'C',
	'setpointMin': 19,
	'setpointMax': 21,
	'failsafeOverride': False
}

# weather
log.info("Starting weather module...")
import darksky
weatherThread = threading.Thread(target=darksky.updateWeather)
weatherThread.name = 'Weather'
weatherThread.daemon = True
weatherThread.start()
log.info("Done.")

# model
log.info("Starting thermostat module...")
import thermostat
thermo = thermostat.Thermostat(preferences)
thermostatThread = threading.Thread(target=thermostat.start,args=[thermo])
thermostatThread.name = 'Thermostat'
thermostatThread.daemon = True
thermostatThread.start()
log.info("Done.")

# server
log.info("Starting server module...")
import server
serverThread = threading.Thread(target=server.start,args=[thermo,preferences])
serverThread.name = 'Server'
serverThread.daemon = True
serverThread.start()
log.info("Done.")

# touchscreen ui, run in main thread
log.info("Starting GUI module...")
import touchscreen
touchscreen.start(thermo, darksky.latestForecast, preferences)