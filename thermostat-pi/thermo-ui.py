#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame as pg
import time
from time import localtime, strftime
import os
import math

PI = 3.14159




pg.init()
pg.font.init()

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

font_l = pg.font.Font("EUROSTIB.ttf", 62)
font_m = pg.font.Font("EUROSTIB.ttf", 40)
font_s = pg.font.Font("EUROSTIB.ttf", 26)
font_ss = pg.font.Font("EUROSTIB.ttf", 18)

icons = pg.image.load('Climacons.png')

units = 'C'

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

lcd = pg.display.set_mode((320, 240))
pg.mouse.set_visible(True) # todo should be false for touch

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
	label = font.render(text, 1, color)
	# put the label object on the screen at point x=100, y=100
	rect = textSize(text, font, point, hanchor, vanchor)

	lcd.blit(label, rect)

def convert(t):
	if units == 'F':
		return t * 9.0 / 5.0 + 32.0
	else:
		return t

def tempstr(t):	
	return u"%2.1f" % t


def drawUI(temp, state, conditions, setpoint, cooldown):

	setpoint = (convert(setpoint[0]), convert(setpoint[1]))

	# in the default state, the ui consists of:
	# current temperature circle
		# colored based on state
		# black text
		# white ring around the outside for cooldown
	pg.draw.circle(lcd, statecolor, (160,120), in_r, 0)

	if temp:
		drawText(tempstr(convert(temp)), font_l, (160,120), 'center', 'center', black)
		drawText(u"˚" + units, font_s, (155,170), 'center', 'center', black)
	else:
		drawText("ERR", font_l, (160,120), 'center', 'center', black)
		drawText('ON' if failsafeOverride else 'OFF', font_s, (160,170), 'center', 'center', black)

	if cooldown > 0:
		rads = cooldown * PI * 2
		pg.draw.arc(lcd, white, pg.Rect(160-out_r, 120-out_r,out_r*2,out_r*2), PI/2.0 - rads,PI/2.0, 4)
		arcend = (int(160 + math.sin(rads) * out_r), int(120 - math.cos(rads) * out_r))
		pg.draw.circle(lcd, white, arcend, 8, 0)

	# current outside conditions
		# climacon and temperature
	try:
		iconorigin = iconpixels[conditions['icon']]
	except KeyError:
		iconorigin = 64, 64*5 # fallback circle
	lcd.blit(icons, (5,5), pg.Rect(iconorigin, (64,64)), pg.BLEND_ADD) 
	drawText(tempstr(convert(conditions['temp'])), font_s, (5 + 32,64 + 5), 'center', 'top', white)


	# clock
	timestr = strftime("%H:%M", localtime())
	drawText(timestr, font_s, (5,235), 'left', 'bottom', white)

	if temp:
		drawScale(temp, setpoint)

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
	currentTempY = yForT(convert(temp))
	pg.draw.circle(lcd, statecolor, (320,currentTempY), 10)


def drawSetTemp(temp, setpoint, idx):
	basecolor = red if idx == 1 else blue

	for i in range(-20,40,20):
		color = bright(basecolor) if swipe[1] >= 1 else basecolor
		pg.draw.line(lcd, color, (80,40 - i),(160, 40 - i - 40), 4)
		pg.draw.line(lcd, color, (160,40 - i - 40),(240, 40 - i), 4)

		color = bright(basecolor) if swipe[1] <= -1 else basecolor
		pg.draw.line(lcd, color, (80,200 + i),(160, 200 + i + 40), 4)
		pg.draw.line(lcd, color, (160,200 + i + 40),(240, 200 + i), 4)

	pg.draw.circle(lcd, basecolor, (160,120), in_r, 0)

	drawText('SET', font_s, (160,80), 'center', 'center', black)
	drawText(tempstr(convert(setpoint[idx])), font_l, (160,120), 'center', 'center', black)
	drawText('MAX' if idx == 1 else 'MIN', font_s, (160,165), 'center', 'center', black)


	drawScale(temp, setpoint)


cooldown = 1.0

pressed = False
fingerpos = (0,0)
lastfingerpos = (0,0)

swipe = [0,0]

state = 'normal'
stateTimeout = 0

# for demo
temp = 19.2
setpoint = [18.0,20.0]
conditions = {'icon': 'snow', 'temp': -2.4}
thermostatstate = 'heating'
#alerts = ["Blizard Warning", 'High Wind Watch']
alerts = []
failsafeOverride = True

animate = 0
t = 0

done = False
while not done:
	dt = 1.0 / 60.0;
	t += dt

	dpos = (lastfingerpos[0] - fingerpos[0], lastfingerpos[1] - fingerpos[1])
	lastfingerpos = fingerpos


	region = ''	
	centerrel = (fingerpos[0] - 160, fingerpos[1] - 120)
	if math.sqrt(centerrel[0] * centerrel[0] + centerrel[1] * centerrel[1]) < in_r:
		region = 'center'
	elif centerrel[0] > in_r and centerrel[1] < 0:
		region = 'max'
	elif centerrel[0] > in_r and centerrel[1] >= 0:
		region = 'min'


	for event in pg.event.get():
		if event.type == pg.QUIT:
			done = True
		elif(event.type is pg.MOUSEBUTTONDOWN):
			fingerpos = pg.mouse.get_pos()
			pressed = True
		elif(event.type is pg.MOUSEBUTTONUP):
			fingerpos = pg.mouse.get_pos()
			pressed = False

			# process taps
			if region == 'center' and state == 'normal':
				if temp:
					units = 'C' if units == 'F' else 'F'
				else:
					failsafeOverride = not failsafeOverride
					thermostatstate = 'heating' if failsafeOverride else 'idle'
			elif region == 'max':
				state = 'setmax'
				stateTimeout = 3
			elif region == 'min':
				state = 'setmin'
				stateTimeout = 3

		elif(event.type is pg.MOUSEMOTION):
			fingerpos = pg.mouse.get_pos()


			if state == 'setmax':
				change = int(float(swipe[1]) / 10.0)
				if change != 0:
					swipe[1] -= change * 10
					stateTimeout = 3
					setpoint[1] += change * 0.2
					if setpoint[1] < setpoint[0]:
						setpoint[1] = setpoint[0]
					# todo bounds check
			if state == 'setmin':
				change = int(float(swipe[1]) / 10.0)
				if change != 0:
					swipe[1] -= change * 10
					stateTimeout = 3
					setpoint[0] += change * 0.2
					if setpoint[0] > setpoint[1]:
						setpoint[0] = setpoint[1]
					# todo bounds check


		# touchable regions: 
		# center to switch c/f,

		# max to adjust max,
		# min to adjust min

	lcd.fill((0,0,0))

	# compute our swipe 
	if pressed:
		swipe = [swipe[0] + dpos[0], swipe[1] + dpos[1]]
	else:
		swipe = [0,0]

	# for demo purposes
	cooldown -= dt
	if cooldown < 0:
		cooldown = 0

	# after a certain amount of time, go back to normal display state
	stateTimeout -= dt
	if stateTimeout <= 0:
		stateTimeout = 0
		state = 'normal'

	if thermostatstate == 'heating':
		statecolor = red
	else:
		statecolor = lightgray

	# animated circle
	if state == 'normal' and animate > 0:
		animate -= dt * 700
	if state != 'normal' and animate < 110:
		animate += dt * 700

	if animate < 0:
		animate = 0
		
	pg.draw.circle(lcd, statecolor, (160,120), out_r + int(animate), 4)


	if state == 'normal': 
		drawUI(temp, thermostatstate, conditions, setpoint, cooldown)
	elif state == 'setmin':
		drawSetTemp(temp, setpoint, 0)
	elif state == 'setmax':
		drawSetTemp(temp, setpoint, 1)


	# draw weather alerts
	if len(alerts) > 0:
		box = None
		for alert in alerts:
			alerttext = alert.upper()
			thisbox = textSize(alerttext, font_ss, (160,5), 'center', 'top')
			if box:
				box.left = min(box.left, thisbox.left)
				box.top = min(box.top, thisbox.top)
				box.width = max(box.width, thisbox.width)
				box.height = max(box.height, thisbox.height)			
			else:
				box = thisbox

		alerttext = alerts[int(t / 2) % len(alerts)].upper()
		box.left -= 2
		box.top -= 2
		box.width += 4
		box.height += 4
		pg.draw.rect(lcd, black, box, 0)
		pg.draw.rect(lcd, white, box, 1)
		drawText(alerttext, font_ss, (160,5), 'center', 'top', white)


	if pressed:
		pg.draw.circle(lcd, (255,255,255), fingerpos, 30)



	pg.display.update()


	time.sleep(dt)
