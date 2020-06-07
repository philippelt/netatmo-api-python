#!/usr/bin/python3
# encoding=utf-8

# 2014-01 : philippelt@users.sourceforge.net 

# Just connect to a Netatmo account, and print all last informations available for
# station(s) and modules of the user account
# (except if module data is more than one hour old that usually means module lost
#  wether out of radio range or battery exhausted thus information is no longer
#  significant)

import time
import lnetatmo

authorization = lnetatmo.ClientAuth()
weather = lnetatmo.WeatherStationData(authorization)

user = weather.user

print("Station owner : ", user.mail)
print("Data units    : ", user.unit)

# For each station in the account
for station in weather.stations:

    print("\nSTATION : %s\n" % weather.stations[station]["station_name"])

    # For each available module in the returned data of the specified station
    # that should not be older than one hour (3600 s) from now
    for module, moduleData in weather.lastData(station=station, exclude=3600).items() :
       
        # Name of the module (or station embedded module)
        # You setup this name in the web netatmo account station management
        print(module)
        
        # List key/values pair of sensor information (eg Humidity, Temperature, etc...)
        for sensor, value in moduleData.items() :
            # To ease reading, print measurement event in readable text (hh:mm:ss)
            if sensor == "When" : value = time.strftime("%H:%M:%S",time.localtime(value))
            print("%30s : %s" % (sensor, value))


# OUTPUT SAMPLE :
#
# $ printAllLastData
#
#Station owner :  ph.larduinat@wanadoo.fr
#Data units    :  metric
#
#
#STATION : TEST-STATION-1
#
#Office
#    AbsolutePressure : 988.7
#                 CO2 : 726
#       date_max_temp : 1400760301
#       date_min_temp : 1400736146
#            Humidity : 60
#            max_temp : 19.6
#            min_temp : 17.9
#               Noise : 46
#            Particle : 12768
#            Pressure : 988.7
#         Temperature : 19.6
#                When : 14:10:01
#Outdoor
#          battery_vp : 5200
#                 CO2 : 555
#       date_max_temp : 1400759951
#       date_min_temp : 1400732524
#            Humidity : 75
#            max_temp : 17.9
#            min_temp : 10.3
#           rf_status : 57
#         Temperature : 17.9
#                When : 14:09:25
#Greenhouse
#      date_min_temp : 1400732204
#            Humidity : 89
#            max_temp : 19.9
#            min_temp : 9.1
#           rf_status : 83
#         Temperature : 19.9
#                When : 14:09:12
