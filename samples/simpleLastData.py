#!/usr/bin/python3
# encoding=utf-8

# 2013-01 : philippelt@users.sourceforge.net 

# Just connect to a Netatmo account, and print internal and external temperature of the default (or single) station
# In this case, sensors of the station and the external module have been named 'internal' and 'external' in the
# Account station settings.

import lnetatmo

authorization = lnetatmo.ClientAuth()
devList = lnetatmo.WeatherStationData(authorization)

print ("Current temperature (inside/outside): %s / %s °C" %
        ( devList.lastData()['internal']['Temperature'],
          devList.lastData()['external']['Temperature'])
      )

