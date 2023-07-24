#!/usr/bin/python3
# encoding=utf-8

# 2013-01 : philippelt@users.sourceforge.net 

# Simple example run in a cron job (every 30' for example) to send an alarm SMS if some condition is reached
# and an other SMS when condition returned to normal. In both case, a single SMS is emitted to multiple
# peoples (here phone1 and phone2 are two mobile phone numbers)
# Note : lsms is my personnal library to send SMS using a GSM modem, you have to use your method/library

import sys, os
import lnetatmo,lsms

MARKER_FILE = "/<somewhere>/TempAlarm"   # This flag file will be used to avoid sending multiple SMS on the same event
                                         # Remember that the user who run the cron job must have the rights to create the file

# Access the station
authorization = lnetatmo.ClientAuth()
devList = lnetatmo.WeatherStationData(authorization)

message = []

# Condition 1 : the external temperature is below our limit
curT = devList.lastData()['external']['Temperature']
if curT < 5 : message.append("Temperature going below 5°C")

# Condition 2 : The external temperature data is older that 1 hour
someLost = devList.checkNotUpdated()
if someLost and 'external' in someLost : message.append("Sensor is no longer active")

# Condition 3 : The outdoor module battery is dying
volts = devList.lastData()['external']['battery_vp'] # I suspect that this is the total Voltage in mV
if volts < 5000 : message.append("External module battery needs replacement") # I will adjust the threshold over time

# If one condition is present, at least, send an alarm by SMS
if message :
    if not os.path.exists(MARKER_FILE) :
        message = "WEATHER ALERT\n" + "\n".join(message)
        for p in ('<phone1>', '<phone2>') :
            lsms.sendSMS(p, message, flash=True)
        open(MARKER_FILE,"w").close() # Just to create the empty marker file and avoid to resend the same alert
else :
    if os.path.exists(MARKER_FILE) :
        os.remove(MARKER_FILE)
        for p in ('<phone1>', '<phone2>') :
            lsms.sendSMS(p, "END of WEATHER alert, current temperature is %s°C" % curT)

sys.exit(0)
