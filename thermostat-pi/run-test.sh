#/usr/bin/bash

export LD_LIBRARY_PATH=/usr/local/lib
export TSLIB_PLUGINDIR=/usr/local/lib/ts
export TSLIB_FBDEV=/dev/fb1
export TSLIB_TSDEVICE=/dev/input/event0 
export SDL_MOUSEDRV=TSLIB 
export SDL_MOUSEDEV=/dev/input/event0 
export SDL_NOMOUSE=1 
export SDL_FBDEV=/dev/fb1

cd /home/pi

/usr/bin/python touchscreen.py

