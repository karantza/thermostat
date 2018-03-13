# -*- coding: utf-8 -*-

from utility import *

import pygame as pg
import time
import datetime
import pytz
import tzlocal
from time import localtime, strftime
import math
import forecastio
from tzlocal import get_localzone # $ pip install tzlocal


PI = 3.14159

log.debug("initializing graphics...")
pg.init()
pg.font.init()
lcd = pg.display.set_mode((320, 240))

pg.mouse.set_visible(False)

black = (0,0,0)
white = (255,255,255)
gray = (60,60,60)
red = (241,90,41)
blue = (41,90,241)
lightgray = (150,150,150)

def bright(c):
	return tuple([(x + 255)/2 for x in c])

in_r = 80
out_r = 90

statecolor = lightgray

log.debug("Loading fonts...")
font_l = pg.font.Font("EUROSTIB.ttf", 62)
font_m = pg.font.Font("EUROSTIB.ttf", 40)
font_s = pg.font.Font("EUROSTIB.ttf", 26)
font_ss = pg.font.Font("EUROSTIB.ttf", 18)

log.debug("Loading icons...")
icons = pg.image.load('Climacons.png')

iconmap = {
	'clear-day': (1,4),
	'clear-night': (6, 4),
	'rain': (0, 1),
	'snow':  (2, 2),
	'sleet': (6, 1),
	'wind': (4, 3),
	'fog': (8, 2),
	'cloudy': (0, 0),
	'partly-cloudy-day': (2, 0),
	'partly-cloudy-night': (3, 0),
}

# scale the icon ids up to pixel positions
iconpixels = { k: (iconmap[k][0] * 64, iconmap[k][1] * 64) for k in iconmap }

def datetime_from_utc_to_local(utc_datetime):
	return utc_datetime.replace(tzinfo=pytz.utc).astimezone(tzlocal.get_localzone())

# draw some text into an area of a surface
# automatically wraps words
# returns any text that didn't get blitted
def drawWrappedText(surface, text, color, rect, font, aa=False, bkg=None):
    y = rect.top
    lineSpacing = -2

    # get the height of the font
    fontHeight = font.size("Tg")[1]

    while text:
        i = 1

        # determine if the row of text will be outside our area
        if y + fontHeight > rect.bottom:
            break

        # determine maximum width of line
        while font.size(text[:i])[0] < rect.width and i < len(text):
            i += 1

        # if we've wrapped the text, then adjust the wrap to the last word      
        if i < len(text): 
            i = text.rfind(" ", 0, i) + 1

        # render the line and blit it to the surface
        if bkg:
            image = font.render(text[:i], 1, color, bkg)
            image.set_colorkey(bkg)
        else:
            image = font.render(text[:i], aa, color)

        surface.blit(image, (rect.left, y))
        y += fontHeight + lineSpacing

        # remove the text we just blitted
        text = text[i:]

    return text

def textSize(text, font, point, hanchor, vanchor):
	textsize = font.size(text)

	if hanchor == 'left':
		right = point[0]
	if hanchor == 'center':
		right = point[0] - textsize[0] / 2 
	if hanchor == 'right':
		right = point[0] - textsize[0]

	if vanchor == 'top':
		top = point[1]
	if vanchor == 'center':
		top = point[1] - textsize[1] / 2 
	if vanchor == 'bottom':
		top = point[1] - textsize[1]

	return pg.Rect(right, top, textsize[0], textsize[1])

def drawText(text, font, point, hanchor, vanchor, color):
	label = font.render(text, True, color)
	# put the label object on the screen at point x=100, y=100
	rect = textSize(text, font, point, hanchor, vanchor)

	lcd.blit(label, rect)

def drawIcon(icon, pos):
	try:
		iconorigin = iconpixels[icon]
	except KeyError:
		iconorigin = 64, 64*5 # fallback circle
	lcd.blit(icons, pos, pg.Rect(iconorigin, (64,64)), pg.BLEND_ADD) 


def start(thermostat, latestWeather, prefs):
	log.info("GUI initializing...")

	def drawUI(temp, conditions, setpoint, cooldown):

		setpoint = (convert(prefs['units'], setpoint[0]), convert(prefs['units'], setpoint[1]))

		# in the default state, the ui consists of:
		# current temperature circle
			# colored based on state
			# black text
			# white ring around the outside for cooldown
		pg.draw.circle(lcd, statecolor, (160,120), in_r, 0)

		if temp:
			drawText(tempstr(convert(prefs['units'], temp)), font_l, (160,120), 'center', 'center', black)
			drawText(u"˚" + prefs['units'], font_s, (155,170), 'center', 'center', black)
		else:
			drawText("ERR", font_l, (160,120), 'center', 'center', black)
			drawText('ON' if prefs['failsafeOverride'] else 'OFF', font_s, (160,170), 'center', 'center', black)

		if cooldown > 0:
			rads = cooldown * PI * 2
			pg.draw.arc(lcd, white, pg.Rect(160-out_r, 120-out_r,out_r*2,out_r*2), PI/2.0 - rads,PI/2.0, 4)
			arcend = (int(160 + math.sin(rads) * out_r), int(120 - math.cos(rads) * out_r))
			pg.draw.circle(lcd, white, arcend, 8, 0)

		# current outside conditions
		# climacon and temperature
		drawIcon(conditions.currently().icon, (5,30))
		drawText(tempstr(convert(prefs['units'], conditions.currently().temperature)) + " " + prefs['units'], font_s, (5+32, 5), 'center', 'top', white)


		# clock
		timestr = strftime('%H:%M', localtime())
		drawText(timestr, font_s, (5,235), 'left', 'bottom', white)

		if temp:
			drawScale(temp, setpoint)


		# draw weather alert symbol
		if len(conditions.alerts()) > 0:
			
			alertLevels = {
				'none': 0,
				'advisory': 1,
				'watch': 2,
				'warning': 3
			}

			maxAlert = max([alertLevels[a.severity] for a in conditions.alerts()])

			alertColor = [
				(255,255,255),
				(255,255,0),
				(255,128,0),
				(255,0,0)
			]

			pg.draw.circle(lcd, alertColor[maxAlert], (32,120), 30, 0)
			drawText("!", font_l, (32,120), 'center', 'center', black)

	def drawScale(temp, setpoint):
		# set temp range on the right
			# scale
		pg.draw.line(lcd, white, (320,0), (320,240), 4)


		def yForT(t): 
			if (setpoint[1] == setpoint[0]):
				return 120
			rate = 160 / (setpoint[1] - setpoint[0])
			y = int(200 - rate * (t - setpoint[0]))
			if y < 0:
				y = 0
			if y > 240:
				y = 240
			return y

		ticks = []
		maxtick = int(setpoint[0]) - 5
		while maxtick <= setpoint[1] + 5:
			ticks.append(maxtick)
			maxtick += 0.25
		
		for t in ticks:
			y = yForT(t)
			w = 8 if t == int(t) else 4
			thick = 4 if t == int(t) else 2
			pg.draw.line(lcd, white, (320-w, y), (320, y), thick)

		miny = 200
		maxy = 40
		drawText('MIN', font_s, (320 - 15, miny + 20), 'right', 'center', blue)
		drawText(tempstr(setpoint[0]), font_s, (320 - 15, miny), 'right', 'center', blue)
		
		drawText('MAX', font_s, (320 - 15, maxy - 20), 'right', 'center', red)
		drawText(tempstr(setpoint[1]), font_s, (320 - 15, maxy), 'right', 'center', red)
		
		# draw the current temperature dot
		currentTempY = yForT(convert(prefs['units'], temp))
		pg.draw.circle(lcd, statecolor, (320,currentTempY), 10)

	def drawSetTemp(temp, setpoint, idx):
		setpoint = (convert(prefs['units'], setpoint[0]), convert(prefs['units'], setpoint[1]))

		basecolor = red if idx == 1 else blue

		color = white

		dy = 50
		pg.draw.polygon(lcd, white, [(80,dy),(160, dy - 40),(240, dy),(160, dy - 20)])
		dy = 190
		pg.draw.polygon(lcd, white, [(80,dy),(160, dy + 40),(240, dy),(160, dy + 20)])
		
		pg.draw.circle(lcd, basecolor, (160,120), in_r, 0)

		drawText('SET', font_s, (160,80), 'center', 'center', black)
		drawText(tempstr(setpoint[idx]), font_l, (160,120), 'center', 'center', black)
		drawText('MAX' if idx == 1 else 'MIN', font_s, (160,165), 'center', 'center', black)


		drawScale(temp, setpoint)

	def drawAlerts(currentAlert, conditions):

		alertLevels = {
			'none': 0,
			'advisory': 1,
			'watch': 2,
			'warning': 3
		}

		if currentAlert > len(conditions.alerts()):
			currentAlert = 0

		alert = conditions.alerts()[currentAlert]

		alertColor = [
			(255,255,255),
			(255,255,0),
			(255,128,0),
			(255,0,0)
		][alertLevels[alert.severity]]

		pg.draw.circle(lcd, alertColor, (32,32), 30, 0)
		drawText(str(currentAlert+1) + '/' + str(len(conditions.alerts())), font_s, (32,32), 'center', 'center', black)

		drawText(alert.title, font_s, (64,32), 'left', 'center', white)
		drawWrappedText(lcd, alert.description, white, pg.Rect(5, 64, 310, 170), font_ss, aa=True)

	def drawForecast(conditions):

		precipColor = (114, 168, 255)
		tempColor = red
		days = conditions.daily().data

		horiz = [18, 82, 138, 158, 178, 198, 218]

		maxTemp = max([days[i].temperatureHigh for i in range(0,5)]) + 1
		minTemp = min([days[i].temperatureLow for i in range(0,5)]) - 1

		# draw graphs

		# temp graph
		def yForTemp(t):
			return horiz[1] + (horiz[2]-horiz[1]) * (maxTemp - t) / (maxTemp - minTemp)

		for t in range(int(math.floor(minTemp)), int(math.ceil(maxTemp))):
			pg.draw.line(lcd, gray, (0,yForTemp(t)), (320, yForTemp(t)), 1)

		highPoints = [ (i*64+32, yForTemp(days[i].temperatureHigh)) for i in range(0, 5) ]
		lowPoints = [ (i*64+32, yForTemp(days[i].temperatureLow)) for i in range(0, 5) ]

		pg.draw.lines(lcd, red, False, highPoints, 5)
		pg.draw.lines(lcd, blue, False, lowPoints, 5)


		for i in range(0, 5):
			day1 = days[i]
			day2 = days[i+1]
			x1 = i * 64
			x2 = (i+1) * 64


		
		# draw text and stuff
		for i in range(0, 5):
			day = days[i]
			x = i * 64

			dayOfWeek = day.time.strftime('%a %-d')
			
			drawText(dayOfWeek, font_ss, (x+32, 2), 'center', 'top', white)
			
			
			precip = day.precipProbability 

			if precip > 0.015:
				pg.draw.rect(lcd, (0,0,255), pg.Rect(x, horiz[0]+(1-precip) * 64, 64,precip * 64))  
			
			drawIcon(day.icon, (x,horiz[0]))

			drawText('%.1f' % convert(prefs['units'], day.temperatureHigh), font_ss, (x+32, horiz[1]), 'center', 'top', white)
			drawText('%.1f' % convert(prefs['units'], day.temperatureLow), font_ss, (x+32, horiz[2]), 'center', 'bottom', white)

			pg.draw.rect(lcd, blue, pg.Rect(x, horiz[2], day.humidity * 64, horiz[3] - horiz[2]))  
			drawText('%.0f%%' % int(day.humidity * 100), font_ss, (x+32, horiz[2]+2), 'center', 'top', white)
			
			pg.draw.rect(lcd, lightgray, pg.Rect(x, horiz[3], day.cloudCover * 64, horiz[4] - horiz[3]))  
			drawText('%.0f%%' % int(day.cloudCover * 100), font_ss, (x+32, horiz[3]+2), 'center', 'top', white)
			
			drawText('%.0fmph' % int(day.windSpeed), font_ss, (x+32, horiz[4]+2), 'center', 'top', lightgray)

			sunriseTime = datetime_from_utc_to_local(day.sunriseTime)
			sunsetTime = datetime_from_utc_to_local(day.sunsetTime)

			drawText(sunriseTime.strftime('%-H:%M'), font_ss, (x+32, horiz[5]+2), 'center', 'top', (255,255,60))
			drawText(sunsetTime.strftime('%-H:%M'), font_ss, (x+32, horiz[6]+2), 'center', 'top', (255,255,60))

			# sunriseTime

		# dividers
		for i in range(1, 5):
			pg.draw.line(lcd, white, (i*64,0), (i*64, 240), 1)

		for y in horiz:
			pg.draw.line(lcd, white, (0,y), (320, y), 1)

			


	currentAlert = 0

	# should come from thermostat:
	setpoint = []

	cooldown = 0	

	pressed = False
	fingerpos = (0,0)
	lastfingerpos = (0,0)


	state = 'normal'
	stateTimeout = 0

	animate = 0
	t = 0

	backlightTimeOn = 60
	backlight = 100
	lastInteract = time.time()

	done = False

	log.info("GUI initialized.")

	while not done:
		dt = 0.1; # when not animating/etc

		currentTime = time.time()
		currentDatetime = datetime.datetime.now()

		# get info from thermostat
		if thermostat.failsafe:
			temp = None
		else: 
			temp = thermostat.currentTemp 

		cooldown = 1 - (currentTime - thermostat.lastCycle) / thermostat.cycleDuration

		if cooldown < 0:
			cooldown = 0

		setpoint = [prefs['setpointMin'], prefs['setpointMax']]


		# get updated forecast info
		conditions = latestWeather()



		# check backlight
		shouldBacklight = currentTime - lastInteract < backlightTimeOn
		
		# any weather alerts? turn the backlight on every ~30 minutes for 5 minutes
		if len(conditions.alerts()) > 0 and currentDatetime.minute % 30 < 5:
			shouldBacklight = True
		
		if cooldown > 0:
			shouldBacklight = True
		
		backlightTarget = {True:100, False:0}[shouldBacklight];
		if backlightTarget != backlight:
			if backlightTarget > backlight:
				backlight += dt * 100
			else:
				backlight -= dt * 100

			if backlight < 0:
				backlight = 0
			if backlight > 100:
				backlight = 100
			print "Changing backlight: " + str(backlight)

			setBacklight(backlight)



		# figure out where we're tapping
		dpos = (lastfingerpos[0] - fingerpos[0], lastfingerpos[1] - fingerpos[1])
		lastfingerpos = fingerpos

		region = ''	
		centerrel = (fingerpos[0] - 160, fingerpos[1] - 120)

		if state in ['setmin','setmax']:
			if centerrel[0] < -in_r:
				region = 'back'
			elif centerrel[1] < 0 and centerrel[0] < in_r:
				region = 'up'
			elif centerrel[1] > 0 and centerrel[0] < in_r:
				region = 'down'		
			else:
				region = 'back'

		if state in ['setmin', 'setmax', 'normal']:
			if math.sqrt(centerrel[0] * centerrel[0] + centerrel[1] * centerrel[1]) < in_r:
				region = 'center'
			elif centerrel[0] > in_r and centerrel[1] < -40:
				region = 'max'
			elif centerrel[0] > in_r and centerrel[1] >= 40:
				region = 'min'

		if state in ['normal']:				
			if centerrel[0] < -in_r:
				if centerrel[1] < -40:
					region = 'forecast'
				elif centerrel[1] < 40: 
					region = 'alert'
				else: 
					region = 'clock'

		# process events!

		for event in pg.event.get():
			if event.type == pg.QUIT:
				done = True
			elif(event.type is pg.MOUSEBUTTONDOWN):
				fingerpos = pg.mouse.get_pos()

				lastInteract = currentTime
				pressed = True

			elif(event.type is pg.MOUSEBUTTONUP):
				fingerpos = pg.mouse.get_pos()
				pressed = False

				print(state, region)
				# process taps

				# touchable regions: 
				# center to switch c/f,

				if backlight == 100:

					if state == 'normal':
						if region == 'center':
							if temp:
								prefs['units'] = 'C' if prefs['units'] == 'F' else 'F'
								animate = 20
							else:
								prefs['failsafeOverride'] = not prefs['failsafeOverride']
								animate = 20
							savePrefs(prefs)

						elif region == 'max': # max to adjust max,
							state = 'setmax'
							stateTimeout = 3
						elif region == 'min': # min to adjust min
							state = 'setmin'
							stateTimeout = 3
						elif region == 'alert':
							if len(conditions.alerts()) > 0:
								state = 'alert'
								currentAlert = 0
								stateTimeout = 15
						elif region == 'forecast':
							state = 'forecast'
							stateTimeout = 15


					elif state == 'setmin':
						if region == 'back' or region == 'min':
							state = 'normal'
							stateTimeout = 0
						elif region == 'max':
							state = 'setmax'
							stateTimeout = 3
						elif region == 'up' or region == 'down':
							setpoint[0] += 0.5 if region == 'up' else -0.5
							setpoint[0] = min(setpoint[0], setpoint[1])
							prefs['setpointMin'] = setpoint[0]
							stateTimeout = 3
							savePrefs(prefs)
					elif state == 'setmax':
						if region == 'back' or region == 'max':
							state = 'normal'
							stateTimeout = 0
						elif region == 'min':
							state = 'setmin'
							stateTimeout = 3
						elif region == 'up' or region == 'down': # actually adjusting temp
							setpoint[1] += 0.5 if region == 'up' else -0.5
							setpoint[1] = max(setpoint[0], setpoint[1])
							prefs['setpointMax'] = setpoint[1]
							stateTimeout = 3
							savePrefs(prefs)
					elif state == 'alert':
						currentAlert += 1
						stateTimeout = 15
						if currentAlert == len(conditions.alerts()):
							state = 'normal'
							stateTimeout = 0
					elif state == 'forecast':
						state = 'normal'
						stateTimeout = 0


		if pressed or animate > 0:
			dt = 0.01; # when we're interacting or animating go faster

		lcd.fill((0,0,0))


		# after a certain amount of time, go back to normal display state
		stateTimeout -= dt
		if stateTimeout <= 0:
			stateTimeout = 0
			state = 'normal'

		if thermostat.heating:
			statecolor = red
		else:
			statecolor = lightgray
			# todo add support for cooling

		# animated circle
		if state == 'normal' and animate > 0:
			animate -= dt * 700
		if state != 'normal' and animate < 105:
			animate += dt * 700

		if animate < 0:
			animate = 0
			
		pg.draw.circle(lcd, statecolor, (160,120), out_r + int(animate), 4)

		if state == 'normal': 
			drawUI(temp, conditions, setpoint, cooldown)
		elif state == 'setmin':
			drawSetTemp(temp, setpoint, 0)
		elif state == 'setmax':
			drawSetTemp(temp, setpoint, 1)
		elif state == 'alert':
			drawAlerts(currentAlert, conditions)
		elif state == 'forecast':
			drawForecast(conditions)


		# draw tap circle
		if pressed:
			pg.draw.circle(lcd, (255,255,255), fingerpos, 30)

		pg.display.update()

		t += dt
		time.sleep(dt)

if __name__ == "__main__":
	import darksky
	prefs = { 'units':'C',
	'setpointMin': 19,
	'setpointMax': 21,
	'failsafeOverride': False
	}

	start(MockThermostat(), darksky.latestForecast, prefs)
