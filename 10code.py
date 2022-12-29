"""
PINS IN USE
>NeoPixel
->board.D5
>Motor
->board.I2C
>ESP
->board.11-13
ECEG 201 DA 10
David Berry, Matt Lamparter
Updated 11/01/2022
Changed hour and minute positions to accomodate new NeoPixel ring orientation on PCB v 3.1
"""

#Import Libraries
import espFunctions as espFun
import neoPixelFunctions as neoFun
import motorFunctions as motorFun

#Other imports that are needed
import rtc
import board
import time
import json
import math

################################################################# Constants ################################################################

#Wifi and Thingspeak stuff
try:
    from secrets import secrets_Bucknell as secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
NETWORK_NAME = secrets["ssid"]
NETWORK_PASS = secrets["password"]
THINGSPEAK_CHANNEL = 1982409    #Enter Thingspeak Channel ID
THINGSPEAK_API_KEY = 'PHCKIAN7D6ID332O'   #Enter Thingspeak API
I2C = board.I2C()

#NeoPixel settings
NEO_BRIGHTNESS = 0.3

#Determines whether or not debug messages are printed out
DEBUG = False

################################################################# Helper Functions #################################################################

#Helper function to convert string time to datetime
#Function takes UTC time "2022-04-05T19:34:21.002951+00:00" YYYY-MM-DDThh:mm:ss
#Returns int array [Year, Month, Day, Hour, Minute, Seconds]
def ConvertTime(input):
    time = (input.split('-'))
    time = time[:2] + time[2].split('T')
    time = time[:3] + (time[3].split(':')[:3])
    time[5] = math.floor(float((time[5].split('+')[0])))
    for i in range(len(time)-1):
        time[i] = int(time[i])
    return time

#Helper function to Update and Display Temperature
def UpdateTemperature():

    #Get Forecast from https://www.weather.gov
    #Fill in your API call in this function
    forecast_raw = net_tool.api_get('https://api.weather.gov/gridpoints/CTP/100,68/forecast')
    forecast = json.loads(str(forecast_raw))

    #Convert weather to temp
    temp = int((((forecast["properties"])["periods"])[0])["temperature"])

    #Update Temp to ThingSpeak
    request_msg = "https://api.thingspeak.com/update?api_key={}&field{}={}".format(THINGSPEAK_API_KEY,'1',temp)
    net_tool.api_get(request_msg)

    #Set Temperature
    temp_as_a_degree = ((temp/100)*360)

    #Simply sets the motor arm to the position calculated before
    motor_tool.set_position_degrees(temp_as_a_degree)

def DisplayTime():
    #Clear LED Ring to prep for updated time
    neoFun.set_ring_color((0,0,0))

    #Map minutes and hours to NeoPixel ring LEDs (Note:  our ring has 24 LEDs)
    minutePos = math.floor(neoFun.maprange([0,59], [0,23], time_keeper.datetime[4]))
    hourPos = math.floor(neoFun.maprange([0,11], [0,23], ((time_keeper.datetime[3])%12)))
    #Address the case when the hour is 11 as this maps to LED 23 rather than 22 as it should
    if hourPos == 23:
        hourPos = 22
    #Display time on NeoPixel ring
    neoFun.set_pixel((128,128,10), (minutePos)) # minutes displayed as a yellow dot
    neoFun.set_pixel((10,128,128), (hourPos)) # hour displayed as a blue dot
    #if both hour and minute need to occupy the same LED, make that LED white
    if minutePos == hourPos:
        neoFun.set_pixel((128,128,128), minutePos)
################################################################# Startup Code #################################################################

#Sets the neopixel rings brightness
neoFun.set_brightness(NEO_BRIGHTNESS)

#Set color to green
neoFun.set_ring_color((0,20,0))

#'net_tool' will handle all of the basic function of connecting to wifi and communicating with ThingSpeak
#Calling this, automaticly makes it start connecting to the network you specify here
net_tool = espFun.ESP_Tools(NETWORK_NAME, NETWORK_PASS)

#'motor_tool' handles all the motor related functions
#Calling this will automaticly make the motor try and find its home(i.e. try to make a full rotation and end up hitting the stop)
motor_tool = motorFun.ECEGMotor(I2C)

#Calling this will automaticly make the motor try and find its home(i.e. try to make a full rotation and end up hitting the stop peg)
motor_tool.find_home()

# create an RTC object
time_keeper = rtc.RTC()
curTimeMinute = None

#Get Current time
#Fill in your API call here in this function
time_raw = net_tool.api_get('http://worldtimeapi.org/api/timezone/America/New_York')

time_dic = json.loads(time_raw)

#Extract Date and Time
time_init = ConvertTime(time_dic['utc_datetime'])
#Extract Day Of Week
time_init.append(int(time_dic['day_of_week']))
#Extract Day of Year
time_init.append(int(time_dic['day_of_year']))
#Set Daylight savings to automatic
time_init.append(-1)

#Set the RTC to the current date and time *Set hour-4 for NY time
# (year, month, day, hour, minute, second, day-of-week [1-7 = M-Su], day-of-year [0-366], isDaylightSavings? [1,0])
time_keeper.datetime=(time_init[0],time_init[1],time_init[2],(time_init[3]-4)%24,time_init[4],time_init[5],time_init[6],time_init[7],time_init[8])

#Flash the neoPixel to indicate that startup is done

neoFun.set_ring_color((0,0,0))
time.sleep(.005)
neoFun.set_ring_color((0,20,0))
time.sleep(.005)
neoFun.set_ring_color((0,0,0))

#Move the arm to the current temperature in degrees F.  Acceptable range is 0 - 100 (F).  0 F maps to home position (stop peg)
#and 100 F maps to 360 degrees of rotation (opposite side of stop peg).
UpdateTemperature()
curMin = time_keeper.datetime[4]
DisplayTime()
################################################################# Main Loop #################################################################
"""
Every Minute Update Time
Every 10 Minutes Update Forecast and Send data to ThinkSpeak
"""
mn = 0
while(True):
    #Loop to update the current time once every minute
    if(curMin != time_keeper.datetime[4]):
        DisplayTime()
        mn += 1
        curTimeMinute = time_keeper.datetime[4]
    if (mn==10):
        UpdateTemperature()
