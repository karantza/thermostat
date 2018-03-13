#!/usr/bin/env python
# -*- coding: utf-8 -*-

import forecastio
import time

DARKSKY_API_KEY = '89a75653232ead9e9acc0161ccb193a2'
DARKSKY_LOCATION = (42.4269,-71.0633)
DARKSKY_INTERVAL = 15 # in minutes

forecast = None

def latestForecast():
	global forecast

	if forecast == None:
		forecast = getForecast()
	return forecast

def getForecast():
	return forecastio.load_forecast(DARKSKY_API_KEY, *DARKSKY_LOCATION, units='si')

def updateWeather():
	global forecast

	while (True):
		forecast = getForecast()
		time.sleep(DARKSKY_INTERVAL * 60)

if __name__ == "__main__":
	print(str(getForecast().json))