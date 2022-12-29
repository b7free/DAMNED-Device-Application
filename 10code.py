"""
ECEG 201 Fall 2022

PINS IN USE
>NeoPixel
->board.D5

This script will test the three integrated hardware units on your DAMNED PCB:  the ESP WiFi
module, the NeoPixel RGB LED ring, and the stepper motor
We will use several custom libraries created for this course as well as several standard
Adafruit CircuitPyuthon libraries
"""


import espFunctions as espFun
import neoPixelFunctions as neoFun
import board
import time
import busio
from digitalio import DigitalInOut
import motorFunctions
import adafruit_requests as requests
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_lps2x
import terminalio
from adafruit_display_text import label
import adafruit_displayio_sh1107
import displayio
import rtc
import json
import math

#-----------------
#Define some constants and perform some setup for WiFi to confirm the ESP32 module is found and communicating
#with the Feather
try:
    from secrets import secrets_Bucknell as secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    Raise
NETWORK_NAME = secrets[“ssid”]
NETWORK_PASS = secrets[“password”]
THINGSPEAK_CHANNEL = 1970346
THINGSPEAK_API_KEY = R4K2342L26J2GP60
net_tool = espFun.ESP_TOOLS(NETWORK_NAME, NETWORK_PASS)

# Define the Feather M4 pins you will use to communicate with the ESP32-WROOM-32E device
# in addition to the SPI pins
esp32_cs = DigitalInOut(board.D13)
esp32_ready = DigitalInOut(board.D11)
esp32_reset = DigitalInOut(board.D12)
# Set up SPI communications for ESP device
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
# Create an ESP object for WiFi
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

requests.set_socket(socket, esp)
print("ESP32 SPI webclient test")
if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")
print("Firmware vers.", esp.firmware_version)
print("MAC addr:", [hex(i) for i in esp.MAC_address])
TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"
JSON_URL = "http://api.coindesk.com/v1/bpi/currentprice/USD.json"
I2C = board.I2C()
#Scan for wireless networks in range and print the results to the serial monitor
for ap in esp.scan_networks():
    print("\t%s\t\tRSSI: %d" % (str(ap["ssid"], "utf-8"), ap["rssi"]))

#NeoPixel brightness level (0 - 1.0)
NEO_BRIGHTNESS = 0.3

#Create a motor object
myMotor = motorFunctions.ECEGMotor(I2C)
#-----------------

#Here I'm doing setup and just doing everything that only needs/should be done once

#First, turn off any LEDs that may have been left on from the previous code execution
neoFun.set_ring_color((0,0,0))
print("The script is starting.  Now sleep for 2 seconds.")
time.sleep(2)
#Sets the neopixel rings brightness
neoFun.set_brightness(NEO_BRIGHTNESS)

#The ring should then go red, then green, then blue
#This confirms all three elements of each LED are working
neoFun.set_ring_color((20,0,0))
time.sleep(0.5)
neoFun.set_ring_color((0,20,0))
time.sleep(0.5)
neoFun.set_ring_color((0,0,20))
time.sleep(0.5)
neoFun.set_ring_color((0,0,0))

time.sleep(2)

#Flash the neoPixel to indicate that NeoPixel startup is done
x = 10
while(x>1):
    neoFun.set_ring_color((0,0,0))
    time.sleep(.05)
    neoFun.set_ring_color((0,20,0))
    time.sleep(.05)
    neoFun.set_ring_color((0,0,0))
    x -= 1

#Now it's time to attempt connecting to a WiFi networksprint("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except RuntimeError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)
print("My IP address is", esp.pretty_ip(esp.ip_address))

print(
    "IP lookup adafruit.com: %s" % esp.pretty_ip(esp.get_host_by_name("adafruit.com"))
)
print("Ping google.com: %d ms" % esp.ping("google.com"))

# esp._debug = True
print("Fetching text from", TEXT_URL)
r = requests.get(TEXT_URL)
print("-" * 40)
print(r.text)
print("-" * 40)
r.close()

print()
print("Fetching json from", JSON_URL)
r = requests.get(JSON_URL)
print("-" * 40)
print(r.json())
print("-" * 40)
r.close()

print("Done!")

myMotor.move_arm_degrees(360)
myMotor.move_arm_degrees(-207)

i2c = board.I2C()  # uses board.SCL and board.SDA
lps = adafruit_lps2x.LPS25(i2c)
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)

# SH1107 is vertically oriented 64x128
WIDTH = 128
HEIGHT = 64
BORDER = 2

display = adafruit_displayio_sh1107.SH1107(
    display_bus, width=WIDTH, height=HEIGHT, rotation=0
)

# Make the display context
splash = displayio.Group()
display.show(splash)

color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # White

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(
    inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER
)
splash.append(inner_sprite)

# Text
text1 = " Hello DAMNED User"
text_area = label.Label(terminalio.FONT, text=text1, color=0xFFFFFF, x=8, y=8)
splash.append(text_area)
text2 = f'hPa:{lps.pressure:.1f}'
text_area2 = label.Label(
    terminalio.FONT, text=text2, scale=2, color=0xFFFFFF, x=4, y=22
)
splash.append(text_area2)
text3 = f'Temp:{lps.temperature:.1f}C'
text_area3 = label.Label(terminalio.FONT, text=text3, scale=2, color=0xFFFFFF, x=4, y=44)
splash.append(text_area3)


while True:
    pressure = lps.pressure
    percent = (lps.pressure - 999)/34
    degrees = 360 * percent
    print("Pressure: %.2f hPa" % lps.pressure)
    print("Temperature: %.2f C" % lps.temperature)
    time.sleep(1)
    if pressure > 1013.25:
        for i in range(0,24):
            neoFun.set_pixel((231,225,90),i)
            time.sleep(0.1)
        myMotor.move_arm_degrees(-(360-degrees))
        request="https://api.thingspeak.com/update?api_key={}&field{}={}".format(THINGSPEAK_API_KEY,'1',lps.temperature)
        request="https://api.thingspeak.com/update?api_key={}&field{}={}".format(THINGSPEAK_API_KEY,'2',lps.pressure)
        time.sleep(300)
    if pressure < 1013.25:
        for i in range(0,11):
            neoFun.set_pixel((0,0,255),i)
            time.sleep(0.1)
        myMotor.move_arm_degrees(degrees)
        request="https://api.thingspeak.com/update?api_key={}&field{}={}".format(THINGSPEAK_API_KEY,'1',lps.temperature)
        request="https://api.thingspeak.com/update?api_key={}&field{}={}".format(THINGSPEAK_API_KEY,'2',lps.pressure)
        time.sleep(300)

# now run in an infinite loop of snake animations and arm rotations
#while(1):
    #neoFun.animate_snake((0,20,188),6,0,24)
    #myMotor.move_arm_degrees(360)
    #neoFun.animate_snake((255,20,0),6,0,24)
    #myMotor.move_arm_degrees(-360)
request="https://api.thingspeak.com/update?api_key={}&field{}={}".format(THINGSPEAK_API_KEY,'1',lps.temperature)

