#!/usr/bin/env python
# -*- coding: utf8 -*-

from utility import *
import time
import threading
import logging
import sys

CSV_INTERVAL = 5

CSVFILE = "thermostat.csv"


class Thermostat:
	def __init__(self, prefs):
		# configurable parameters

		self.cycleDuration = 300 # this should be 300 seconds for safety

		self.failsafe = False

		self.prefs = prefs # get a copy of prefs

		# internal status
		self.currentTemp = None
		self.lastTempUpdate = time.time()
		self.lastCycle = time.time() - self.cycleDuration # allows it to start up immediately
		self.heating = False


	def setHeat(self, heat):
		if self.heating == heat:
			return # never change to our current value
			
		setRelay(heat)

		self.heating = heat
		self.lastCycle = time.time()
		log.info("Turning heat " + ("ON" if heat else "OFF"))

	def evaluate(self):
		t = time.time()

		if self.currentTemp == None:
			log.warning("Waiting for sensor data")
			return

		shouldFailsafe = t - self.lastTempUpdate > 600

		if shouldFailsafe:
			log.warning("applying failsafe override: " + str(self.prefs['failsafeOverride']))
			self.setHeat(self.prefs['failsafeOverride'])

		if shouldFailsafe and not self.failsafe:
			# haven't heard from the sensor in 10 minutes. There's a problem.
			log.error("Alert: haven't received a sensor update in " + formatDuration(t - self.lastTempUpdate) + ". Entering failsafe mode.")
			self.failsafe = True
			return

		if self.failsafe and not shouldFailsafe:
			log.warning("Sensor connection reestablished, leaving failsafe mode.")
			self.failsafe = False


		# is the thermostat able to cycle?
		if self.lastCycle + self.cycleDuration < t:

			# do we need to cycle?
			if self.heating:
				if self.currentTemp >= self.prefs['setpointMax']:
					self.setHeat(False)
			else:
				if self.currentTemp <= self.prefs['setpointMin']:
					self.setHeat(True)

	def updateTemp(self, temp):
		log.info('current sensor temperature now ' + str(temp) + 'C' )
		self.currentTemp = temp
		self.lastTempUpdate = time.time()

	def status(self):
		t = time.time();
		ago = formatDuration(t - self.lastTempUpdate)
		duration = formatDuration(t - self.lastCycle)
		nextcycle = (self.lastCycle + self.cycleDuration - t)

		if self.failsafe:
			txt = "<p><b>Warning: failsafe mode.</b> Haven't received a sensor update in " + formatDuration(t - self.lastTempUpdate) + ".</p>"
			if self.prefs['failsafeOverride']:
				txt += '<p>Heat is off.</p><p><a href="override?true">Override: start heat</a></p>'
			else:
				txt += '<p>Heat is on.</p><p><a href="override?false">Override: stop heat</a></p>'
		else: 
			txt = '<p>Heat is ' + ('ON' if self.heating else 'off') + ', has been for ' + duration + '</p>'


		if self.currentTemp == None:
			txt += "<p><b>Waiting for sensor data.</b></p>"
		else:
			txt += '<p>Currently ' + str(self.currentTemp) + 'C (updated ' + ago + " ago)</p>"

			if (self.heating):
				txt += '<p>Heat will turn off when T > ' + str(self.prefs['setpointMax']) + 'C'
			else:
				txt += '<p>Heat will turn on when <= ' + str(self.prefs['setpointMin']) + 'C'

			if nextcycle > 0:
				txt += ' and T-' + formatDuration(nextcycle) + '</p>'
		
		return txt



def start(thermo):
	# create csv file for saving temp data
	datafile = open(CSVFILE, 'a')
	lastDataLog = 0

	while True:
		thermo.evaluate()

		# once per minute write to the data log
		if time.time() - lastDataLog > CSV_INTERVAL * 60:
			lastDataLog = time.time()
			datafile.write(','.join([timestamp(),
			                        str(thermo.currentTemp), 
			                        'true' if thermo.heating else 'false', 
			                        str(thermo.prefs['setpointMax']),
			                        str(thermo.prefs['setpointMin'])]) + '\n')
			datafile.flush()
		time.sleep(10) # time between updates


if __name__ == "__main__":
	prefs = { 
		'units':'C',
		'setpointMin': 19,
		'setpointMax': 21,
		'failsafeOverride': False
	}
	thermo = MockThermostat()
	thermo.prefs = prefs
	start(thermo)

	
