"""
coding=utf-8
"""
import time

from . import NoDevice, postRequest, _BASE_URL

_SETTEMP_REQ = _BASE_URL + "api/setthermpoint"
_GETTHERMOSTATDATA_REQ  = _BASE_URL + "api/getthermostatsdata"
_GETHOMESDATA_REQ = _BASE_URL + "api/homesdata"
_GETHOMESTATUS_REQ = _BASE_URL + "api/homestatus"
_SETTHERMMODE_REQ = _BASE_URL + "api/setthermmode"
_SETROOMTHERMPOINT_REQ = _BASE_URL + "api/setroomthermpoint"
_GETROOMMEASURE_REQ = _BASE_URL + "api/getroommeasure"


class HomeData:
    """
    List the Energy devices (relays, thermostat modules and valves)

    Args:
        authData (ClientAuth): Authentication information with a working access Token
    """
    def __init__(self, authData):
        self.getAuthToken = authData.accessToken
        postParams = {
                "access_token": self.getAuthToken
                }
        resp = postRequest(_GETHOMESDATA_REQ, postParams)

        self.rawData = resp['body']['homes']
        self.homes = {d['id']: d for d in self.rawData}
        if not self.homes:
            raise NoDevice("No thermostat available")
        self.modules = dict()
        self.rooms = dict()
        self.schedules = dict()
        self.zones = dict()
        self.setpoint_duration = dict()
        for i in range(len(self.rawData)):
            nameHome = self.rawData[i]['name']
            if 'modules' in self.rawData[i]:
                if nameHome not in self.modules:
                    self.modules[nameHome] = dict()
                self.default_home = self.rawData[i]['name']
                for m in self.rawData[i]['modules']:
                    self.modules[nameHome][m['id']] = m
                if nameHome not in self.rooms:
                    self.rooms[nameHome] = dict()
                if nameHome not in self.schedules:
                    self.schedules[nameHome] = dict()
                if nameHome not in self.zones:
                    self.zones[nameHome] = dict()
                if nameHome not in self.setpoint_duration:
                    self.setpoint_duration[nameHome] = dict()
                if 'therm_setpoint_default_duration' in self.rawData[i]:
                    self.setpoint_duration[nameHome] = self.rawData[i]['therm_setpoint_default_duration']
                if 'rooms' in self.rawData[i]:
                    for r in self.rawData[i]['rooms']:
                        self.rooms[nameHome][r['id']] = r
                if 'therm_schedules' in self.rawData[i]:
                    for s in self.rawData[i]['therm_schedules']:
                        self.schedules[nameHome][s['id']] = s
                for t in range(len(self.rawData[i]['therm_schedules'])):
                    nameSchedule = self.rawData[i]['therm_schedules'][t]['name']
                    if nameSchedule not in self.zones[nameHome]:
                        self.zones[nameHome][nameSchedule] = dict()
                    for z in self.rawData[i]['therm_schedules'][t]['zones']:
                        self.zones[nameHome][nameSchedule][z['id']] = z

    def homeById(self, hid):
        return None if hid not in self.homes else self.homes[hid]

    def homeByName(self, home=None):
        if not home:
            home = self.default_home
        for key, value in self.homes.items():
            if value['name'] == home:
                return self.homes[key]

    def gethomeId(self, home=None):
        if not home:
            home = self.default_home
        for key, value in self.homes.items():
            if value['name'] == home:
                # print(self.homes[key]['id'])
                # print(self.default_home)
                return self.homes[key]['id']

    def getSelectedschedule(self, home=None):
        if not home:
            home = self.default_home
        self.schedule = self.schedules[home]
        for key in self.schedule.keys():
            if 'selected' in self.schedule[key].keys():
                return self.schedule[key]


class HomeStatus(HomeData):
    """
    """
    def __init__(self, authData, home_id=None, home=None):
        self.getAuthToken = authData.accessToken
        # print(self.modules())
        self.home_data = HomeData(authData)
        # print(home_data.modules)
        if home_id:
            self.home_id = home_id
            # print('home_id', self.home_id)
        elif home:
            self.home_id = self.home_data.gethomeId(home=home)
        else:
            self.home_id = self.home_data.gethomeId(home=self.home_data.default_home)
        postParams = {
            "access_token": self.getAuthToken,
            "home_id": self.home_id
            }

        resp = postRequest(_GETHOMESTATUS_REQ, postParams)
        self.rawData = resp['body']['home']
        self.rooms = dict()
        self.thermostats = dict()
        self.valves = dict()
        self.relays = dict()
        for r in self.rawData['rooms']:
            self.rooms[r['id']] = r
        for t in range(len(self.rawData['modules'])):
            if self.rawData['modules'][t]['type'] == 'NATherm1':
                thermostatId = self.rawData['modules'][t]['id']
                if thermostatId not in self.thermostats:
                    self.thermostats[thermostatId] = dict()
                self.thermostats[thermostatId] = self.rawData['modules'][t]
            # self.thermostats[t['id']] = t
        for v in range(len(self.rawData['modules'])):
            if self.rawData['modules'][v]['type'] == 'NRV':
                valveId = self.rawData['modules'][v]['id']
                if valveId not in self.valves:
                    self.valves[valveId] = dict()
                self.valves[valveId] = self.rawData['modules'][v]
        for r in range(len(self.rawData['modules'])):
            if self.rawData['modules'][r]['type'] == 'NAPlug':
                relayId = self.rawData['modules'][r]['id']
                if relayId not in self.relays:
                    self.relays[relayId] = dict()
                self.relays[relayId] = self.rawData['modules'][r]
        if self.rooms != {}:
            self.default_room = list(self.rooms.values())[0]
        if self.relays != {}:
            self.default_relay = list(self.relays.values())[0]
        if self.thermostats != {}:
            self.default_thermostat = list(self.thermostats.values())[0]
        print(self.thermostats)
        if self.valves != {}:
            self.default_valve = list(self.valves.values())[0]

    def roomById(self, rid):
        if not rid:
            return self.default_room
        for key, value in self.rooms.items():
            if value['id'] == rid:
                return self.rooms[key]

    def thermostatById(self, rid):
        if not rid:
            return self.default_thermostat
        for key, value in self.thermostats.items():
            if value['id'] == rid:
                return self.thermostats[key]

    def relayById(self, rid):
        if not rid:
            return self.default_relay
        for key, value in self.relays.items():
            if value['id'] == rid:
                return self.relays[key]

    def valveById(self, rid):
        if not rid:
            return self.default_valve
        for key, value in self.valves.items():
            if value['id'] == rid:
                return self.valves[key]

    def setPoint(self, rid=None):
        """
        Return the setpoint of a given room.
        """
        setpoint = None
        if rid:
            room_data = self.roomById(rid=rid)
        else:
            room_data = self.roomById(rid=None)
        if room_data:
            setpoint = room_data['therm_setpoint_temperature']
        return setpoint

    def setPointmode(self, rid=None):
        """
        Return the setpointmode of a given room.
        """
        setpointmode = None
        if rid:
            room_data = self.roomById(rid=rid)
        else:
            room_data = self.roomById(rid=None)
        if room_data:
            setpointmode = room_data['therm_setpoint_mode']
        return setpointmode

    def getAwaytemp(self, home=None):
        if not home:
            home = self.home_data.default_home
            # print(self.home_data.default_home)
        data = self.home_data.getSelectedschedule(home=home)
        return data['away_temp']

    def getHgtemp(self, home=None):
        if not home:
            home = self.home_data.default_home
        data = self.home_data.getSelectedschedule(home=home)
        return data['hg_temp']

    def measuredTemperature(self, rid=None):
        """
        Return the measured temperature of a given room.
        """
        temperature = None
        print(rid)
        if rid:
            room_data = self.roomById(rid=rid)
        else:
            room_data = self.roomById(rid=None)
        if room_data:
            temperature = room_data['therm_measured_temperature']
        return temperature

    def boilerStatus(self, rid=None):
        boiler_status = None
        print(rid)
        if rid:
            relay_status = self.thermostatById(rid=rid)
        else:
            relay_status = self.thermostatById(rid=None)
        if relay_status:
            boiler_status = relay_status['boiler_status']
        return boiler_status

    def thermostatType(self, home, rid):
        module_id = None
        for key in self.home_data.rooms[home]:
            if key == rid:
                for module_id in self.home_data.rooms[home][rid]['module_ids']:
                    self.module_id = module_id
                    if module_id in self.thermostats:
                        return "NATherm1"
                    if module_id in self.valves:
                        return "NRV"

    def setThermmode(self, home_id, mode):
        postParams = {
            "access_token": self.getAuthToken,
            "home_id": home_id,
            "mode": mode
            }
        resp = postRequest(_SETTHERMMODE_REQ, postParams)
        print(resp)

    def setroomThermpoint(self, home_id, room_id, mode, temp=None):
        postParams = {
            "access_token": self.getAuthToken,
            "home_id": home_id,
            "room_id": room_id,
            "mode": mode,
            }
        if temp is not None:
            postParams['temp'] = temp
        return postRequest(_SETROOMTHERMPOINT_REQ, postParams)


class ThermostatData:
    """
    List the Thermostat devices (relays and thermostat modules)

    Args:
        authData (ClientAuth): Authentication information with a working access Token
    """
    def __init__(self, authData):
        self.getAuthToken = authData.accessToken
        postParams = {
                "access_token" : self.getAuthToken
                }
        resp = postRequest(_GETTHERMOSTATDATA_REQ, postParams)

        self.rawData = resp['body']
        self.devList = self.rawData['devices']
        if not self.devList : raise NoDevice("No thermostat available")
        self.devId = self.devList[0]['_id']
        self.modList = self.devList[0]['modules']
        self.modId = self.modList[0]['_id']
        self.temp = self.modList[0]['measured']['temperature']
        self.setpoint_mode = self.modList[0]['setpoint']['setpoint_mode']
        if self.setpoint_mode == 'manual':
            self.setpoint_temp = self.modList[0]['setpoint']['setpoint_temp']
        else:
            self.setpoint_temp = self.modList[0]['measured']['setpoint_temp']
        self.relay_cmd = int(self.modList[0]['therm_relay_cmd'])
        self.devices = { d['_id'] : d for d in self.rawData['devices'] }
        self.modules = dict()
        self.therm_program_list = dict()
        self.zones = dict()
        self.timetable = dict()
        for i in range(len(self.rawData['devices'])):
            nameDevice=self.rawData['devices'][i]['station_name']
            if nameDevice not in self.modules:
                self.modules[nameDevice]=dict()
            for m in self.rawData['devices'][i]['modules']:
                self.modules[nameDevice][ m['_id'] ] = m
            for p in self.rawData['devices'][i]['modules'][0]['therm_program_list']:
                self.therm_program_list[p['program_id']] = p
            for z in self.rawData['devices'][i]['modules'][0]['therm_program_list'][0]['zones']:
                self.zones[z['id']] = z
            for o in self.rawData['devices'][i]['modules'][0]['therm_program_list'][0]['timetable']:
                self.timetable[o['m_offset']] = o
        self.default_device = list(self.devices.values())[0]['station_name']

        self.default_module = list(self.modules[self.default_device].values())[0]['module_name']

    def lastData(self, device=None, exclude=0):
        s = self.deviceByName(device)
        if not s : return None
        lastD = dict()
        zones = dict()
        # Define oldest acceptable sensor measure event
        limit = (time.time() - exclude) if exclude else 0
        dm = s['modules'][0]['measured']
        ds = s['modules'][0]['setpoint']['setpoint_mode']
        dz = s['modules'][0]['therm_program_list'][0]['zones']
        for module in s['modules']:
            dm = module['measured']
            ds = module['setpoint']['setpoint_mode']
            dz = module['therm_program_list'][0]['zones']
            if dm['time'] > limit :
                lastD[module['module_name']] = dm.copy()
                lastD[module['module_name']]['setpoint_mode'] = ds
                # For potential use, add battery and radio coverage information to module data if present
                for i in ('battery_vp', 'rf_status', 'therm_relay_cmd', 'battery_percent') :
                    if i in module : lastD[module['module_name']][i] = module[i]
                zones[module['module_name']] = dz.copy()
        return lastD

    def deviceById(self, did):
        return None if did not in self.devices else self.devices[did]

    def deviceByName(self, device):
        if not device: device = self.default_device
        for key,value in self.devices.items():
            if value['station_name'] == device:
                return self.devices[key]

    def moduleById(self, mid):
        for device,mod in self.modules.items():
            if mid in self.modules[device]:
                return self.modules[device][mid]
        return None

    def moduleByName(self, module=None, device=None):
        if not module and not device:
            return self.default_module
        elif device and module:
            if device not in self.modules:
                return None
            for mod_id in self.modules[device]:
                if self.modules[device][mod_id]['module_name'] == module:
                    return self.modules[device][mod_id]
        elif not device and module:
            for device, mod_ids in self.modules.items():
                for mod_id in mod_ids:
                    if self.modules[device][mod_id]['module_name'] == module:
                        return self.modules[device][mod_id]
        else:
            return list(self.modules[device].values())[0]
        return None

    def setthermpoint(self, mode, temp, endTimeOffset):
        postParams = {"access_token": self.getAuthToken}
        postParams['device_id'] = self.devId
        postParams['module_id'] = self.modId
        postParams['setpoint_mode'] = mode
        if mode == "manual":
            postParams['setpoint_endtime'] = time.time() + endTimeOffset
            postParams['setpoint_temp'] = temp
        return postRequest(_SETTEMP_REQ, postParams)
