"""
coding=utf-8
"""
import time

from . import NoDevice, postRequest, _BASE_URL

_SETTEMP_REQ = _BASE_URL + "api/setthermpoint"
_GETTHERMOSTATDATA_REQ  = _BASE_URL + "api/getthermostatsdata"

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
        self.setpoint_temp = self.modList[0]['measured']['setpoint_temp']
        self.setpoint_mode = self.modList[0]['setpoint']['setpoint_mode']
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
                lastD[module['module_name']] = dm.copy()                # lastD['setpoint_mode'] = ds
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
