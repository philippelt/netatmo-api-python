#!/usr/bin/python3
# encoding=utf-8

# 2018-02 : ph.larduinat@wanadoo.fr

# Thermostat basic sample

import sys
import lnetatmo

authorization = lnetatmo.ClientAuth()
thermostat = lnetatmo.ThermostatData(authorization)


defaultThermostat = thermostat.getThermostat()
if not defaultThermostat : sys.exit(1)
defaultModule = thermostat.defaultModule

print('Thermostat name      :', defaultThermostat['name'])
print('Default module       :', defaultModule['name'])
print('Module measured temp :', defaultModule['measured']['temperature'])
print('Module set point     :', defaultModule['measured']['setpoint_temp'])
print('Module battery       : %s%%' % defaultModule['battery_percent'])
for p in defaultModule['therm_program_list']:
    print("\tProgram: ", p['name'])
    for z in p['zones']:
        name = z['name'] if 'name' in z else '<noname>'
        print("\t%15s : %s" % (name, z['temp']))
