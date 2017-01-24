# Author: Tony Norman - 2016
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import ili9341
import time
from PIL import Image, ImageFont, ImageDraw

# Raspberry Pi configuration.
DC = 18
RST = 23
SPI_PORT = 0
SPI_DEVICE = 0
SOLENOID = 24	# solenoid pin

def nixie(char,char_width):
	""" pastes the appropriate nixie png into supplied image"""
	if char>='0' and char <='9':
		fname = char + '.png'
	elif char == '-':
		fname = 'dash.png'
	elif char == '.':
		fname = 'dot.png'
	else:
		fname = 'off.png'
	
	img1 = Image.open('/home/pi/python/nixie/' + fname)
	w, h = img1.size
	img1 = img1.resize((char_width, char_width*h/w))
	w, h = img1.size
	return (img1, h)

def dec_to_digit_strings(val):
	""" converts a two digit integer to two single character strings"""
	d1 = str(unichr((val/10) +0x30))
	d2 = str(unichr((val%10) +0x30))
	return d1,d2

# setup gpio
gpio = GPIO.get_platform_gpio()
# set the solenoid pin to output
gpio.setup(SOLENOID,GPIO.OUT)

# solenoid off
gpio.output(SOLENOID, False)


def chime(t):
	gpio.output(SOLENOID, True)
	time.sleep(t)
	gpio.output(SOLENOID, False)

def chimes(z):
	for x in range(z):
		chime(0.1)		
		time.sleep(1)

# Create TFT LCD display class.
disp = ili9341.ili9341(DC, rst=RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=64000000))

# Initialize display.
disp.begin()

# set the rgb values for the background color
red = 253
green = 206
blue = 45
disp._bground = ili9341.color565(red,green,blue)
disp.set_rotation(3)
# foreground color
disp._color = 0xffff

# clear the screen
disp.fill_screen(disp._bground)

# get the image for the dots in the middle of the display
dot = Image.open('/home/pi/python/filament.png')
# change width
dot_width = 16
dot = dot.resize((dot_width,dot_width))

colon_x = disp.width/2-dot_width/2
colon_y1 = 140
colon_y2 = 180

# make some blanking images the size of the filament
im = Image.open('/home/pi/python/clockwork.png')
blank1 = im.crop((colon_x, colon_y1, colon_x+dot_width, colon_y1+dot_width))
blank2 = im.crop((colon_x, colon_y2, colon_x+dot_width, colon_y2+dot_width))


lastmin = 100		# remember the last 'minute number'
colon = True		# set the colon image to dot - visible
border = 10			# keep 10 pixels from the edge of the display

# set the true-type font
disp._font = ImageFont.truetype('/home/pi/python/Lekton-Regular.ttf', 60)
# set the font color
disp._color = ili9341.color565(255,189,56)

# chime three times on startup - just because...
chimes(3)

while 1:
	# get the current time
	t = time.localtime()
	
	# if the time has changed
	if lastmin != t.tm_min:
		char_width = 70		# width of the 'nixie tube' image display in pixels
		
		# make a new full-screen image using the background color
		# im = Image.new('RGB', (disp.width, disp.height), ili9341.color_rgb(disp._bground))
		im = Image.open('/home/pi/python/clockwork.png')
		banner = Image.new('RGBA', (320, 240),(0,0,0,100))
		im.paste(banner, (0,0), mask=banner)

		# get the hour as two string characters
		h,l = dec_to_digit_strings(t.tm_hour)
		# get the 'nixie' image for the tens
		n_image , height = nixie(h, char_width)
		# paste it into the base image
		im.paste(n_image, (border, disp.height - height - border), mask=n_image)
		# get the 'nixie' image for the units
		n_image , height = nixie(l, char_width)
		# paste it into the base image
		im.paste(n_image, (char_width+border, disp.height - height - border), mask=n_image)
		
		
		# get the minute as two string characters
		h,l = dec_to_digit_strings(t.tm_min)
		# add the 'nixie' image for each one to the base image
		# get the 'nixie' image for the tens
		n_image , height = nixie(h, char_width)
		# paste it into the base image
		im.paste(n_image, (disp.width-char_width*2 - border, disp.height - height - border), mask=n_image)
		# get the 'nixie' image for the units
		n_image , height = nixie(l, char_width)
		# paste it into the base image
		im.paste(n_image, (disp.width-char_width - border, disp.height - height - border), mask=n_image)

		# get the current date in an image
		img, width, height = disp.text(time.strftime('%a %d %b'))
		# paste the image at the top of the base image
		im.paste(img, ((disp.width-width)/2 + border, border), mask=img)
		
		# display the image
		disp.p_image(0, 0, im)
		
		# if we are on the hour then chime the hour
		if t.tm_min == 0:
			strikes = t.tm_hour
			if strikes == 0:
				strikes = 12
			if strikes > 12:
				strikes -= 12
			chimes(strikes)		# chime 12 hour clock - we don't want it striking 23!

		# if we are on the half hour then chime once
		if t.tm_min == 30:
			chimes(1)

		# update the last minute so we can test for change
		lastmin = t.tm_min
		
	# if the colon was visible last time then hide it
	# and vice versa
	colon = not colon
	# either display the colon
	if colon:
		disp.p_image(colon_x, colon_y1, dot)
		disp.p_image(colon_x, colon_y2, dot)
	# or display the blank images to hide it
	else:
		disp.p_image(colon_x, colon_y1, blank1)
		disp.p_image(colon_x, colon_y2, blank2)
		
	# sleep for a second	
	time.sleep(1)

