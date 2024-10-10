# Published Jan 2013
# Author : Philippe Larduinat, ph.larduinat@wanadoo.fr
# Multiple contributors : see https://github.com/philippelt/netatmo-api-python
# License : GPL V3
"""
This API provides access to the Netatmo weather station or/and the Welcome camera
This package can be used with Python2 or Python3 applications and do not
require anything else than standard libraries

PythonAPI Netatmo REST data access
coding=utf-8
"""

import warnings
if __name__ == "__main__": warnings.filterwarnings("ignore")                              # For installation test only

from sys import version_info
from os import getenv
from os.path import expanduser, exists
import platform
import json, time
import imghdr
import warnings
import logging

# Just in case method could change
PYTHON3 = (version_info.major > 2)

# HTTP libraries depends upon Python 2 or 3
if PYTHON3 :
    import urllib.parse, urllib.request
else:
    from urllib import urlencode
    import urllib2


######################## AUTHENTICATION INFORMATION ######################

# To be able to have a program accessing your netatmo data, you have to register your program as
# a Netatmo app in your Netatmo account. All you have to do is to give it a name (whatever) and you will be
# returned a client_id and secret that your app has to supply to access netatmo servers.

# To ease Docker packaging of your application, you can setup your authentication parameters through env variables

# Authentication:
#  1 - Values defined in environment variables : CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN
#  2 - Parameters passed to ClientAuth initialization
#  3 - The .netatmo.credentials file in JSON format in your home directory (now mandatory for regular use)

# Note that the refresh token being short lived, using envvar will be restricted to speific testing use case

#########################################################################


# Common definitions

_BASE_URL = "https://api.netatmo.com/"
_AUTH_REQ              = _BASE_URL + "oauth2/token"
_GETMEASURE_REQ        = _BASE_URL + "api/getmeasure"
_GETSTATIONDATA_REQ    = _BASE_URL + "api/getstationsdata"
_GETTHERMOSTATDATA_REQ = _BASE_URL + "api/getthermostatsdata"
_GETHOMEDATA_REQ       = _BASE_URL + "api/gethomedata"
_GETCAMERAPICTURE_REQ  = _BASE_URL + "api/getcamerapicture"
_GETEVENTSUNTIL_REQ    = _BASE_URL + "api/geteventsuntil"
_HOME_STATUS           = _BASE_URL + "api/homestatus"                                     # Used for Home+ Control Devices 
_GETHOMES_DATA         = _BASE_URL + "api/homesdata"                                      # New API
_GETHOMECOACH          = _BASE_URL + "api/gethomecoachsdata"                              #

#TODO# Undocumented (but would be very usefull) API : Access currently forbidden (403)

_POST_UPDATE_HOME_REQ  = _BASE_URL + "/api/updatehome"

# For presence setting (POST BODY):
# _PRES_BODY_REC_SET     = "home_id=%s&presence_settings[presence_record_%s]=%s"          # (HomeId, DetectionKind, DetectionSetup.index)
_PRES_DETECTION_KIND   = ("humans", "animals", "vehicles", "movements")
_PRES_DETECTION_SETUP  = ("ignore", "record", "record & notify")

# _PRES_BODY_ALERT_TIME  = "home_id=%s&presence_settings[presence_notify_%s]=%s"          # (HomeID, "from"|"to", "hh:mm")

# Regular (documented) commands (both cameras)

_PRES_CDE_GET_SNAP     = "/live/snapshot_720.jpg"

#TODO# Undocumented (taken from https://github.com/KiboOst/php-NetatmoCameraAPI/blob/master/class/NetatmoCameraAPI.php)
# Work with local_url only (undocumented scope control probably)

# For Presence camera

_PRES_CDE_GET_LIGHT    = "/command/floodlight_get_config"
# Not working yet, probably due to scope restriction
#_PRES_CDE_SET_LIGHT    = "/command/floodlight_set_config?config=mode:%s"                 # "auto"|"on"|"off"


# For all cameras

_CAM_CHANGE_STATUS     = "/command/changestatus?status=%s"                                # "on"|"off"
# Not working yet
#_CAM_FTP_ACTIVE        = "/command/ftp_set_config?config=on_off:%s"                      # "on"|"off"

#Known TYPE used by Netatmo services + API,      there can be more types possible
TYPES = {
    'BFII'         : ["Bticino IP Indoor unit", 'Home + Security'],
    'BFIC'         : ["Bticino IP Guard station", 'Home + Security'],
    'BFIO'         : ["Bticino IP Entrance panel", 'Home + Security'],
    'BFIS'         : ["Bticino Server DES", 'Home + Security'],
    'BNS'          : ["Smarther with Netatmo Thermostat", 'Home+Control'],
    'BNCU'         : ["Bticino Bticino Alarm Central Unit", 'Home + Security'],
    'BNCS'         : ["Bticino module Controlled Socket", 'Home+Control'],
    'BNCX'         : ["Bticino Class 300 EOS", 'Home + Security'],
    'BNDL'         : ["Bticino Doorlock", 'Home + Security'],
    'BNEU'         : ["Bticino external unit", 'Home + Security'],
    'BNFC'         : ["Bticino Thermostat", 'Home+Control'],
    'BNMH'         : ["Bticino My Home Server 1", 'Home + Security'],                     # also API Home+Control  GATEWAY
    'BNSE'         : ["Bticino Alarm Sensor", 'Home + Security'],
    'BNSL'         : ["Bticino Staircase Light", 'Home + Security'],
    'BNTH'         : ["Bticino Thermostat", 'Home+Control'],
    'BNTR'         : ["Bticino module towel rail", 'Home+Control'],
    'BNXM'         : ["Bticino X meter", 'Home+Control'],

    'NACamera'     : ["indoor camera", 'Home + Security'],
    'NACamDoorTag' : ["door tag", 'Home + Security'],
    'NAMain'       : ["weather station", 'Weather'],
    'NAModule1'    : ["outdoor unit", 'Weather'],
    'NAModule2'    : ["wind unit", 'Weather'],
    'NAModule3'    : ["rain unit", 'Weather'],
    'NAModule4'    : ["indoor unit", 'Weather'],
    'NAPlug'       : ["thermostat relais station", 'Energy'],                             # A smart thermostat exist of a thermostat and a Relais module
                                                                                          # The relais module is also the bridge for thermostat and Valves
    'NATherm1'     : ["thermostat",  'Energy'],
    'NCO'          : ["co2 sensor", 'Home + Security'],                                   # The same API as smoke sensor
    'NDB'          : ["doorbell", 'Home + Security'],
    'NOC'          : ["outdoor camera", 'Home + Security'],
    'NRV'          : ["thermostat valves", 'Energy'],                                     # also API Home+Control
    'NSD'          : ["smoke sensor", 'Home + Security'],
    'NHC'          : ["home coach", 'Aircare'],
    'NIS'          : ["indoor sirene", 'Home + Security'],

    'NLC'          : ["Cable Outlet", 'Home+Control'],
    'NLE'          : ["Ecometer", 'Home+Control'],
    'NLG'          : ["Gateway", 'Home+Control'],
    'NLGS'         : ["Standard DIN Gateway", 'Home+Control'],
    'NLP'          : ["Power Outlet", 'Home+Control'],
    'NLPC'         : ["DIN Energy meter", 'Home+Control'],
    'NLPD'         : ["Dry contact", 'Home+Control'],
    'NLPM'         : ["Mobile Socket", 'Home+Control'],
    'NLPO'         : ["Contactor", 'Home+Control'],
    'NLPT'         : ["Teleruptor", 'Home+Control'],

    'OTH'          : ["Opentherm Thermostat Relay", 'Home+Control'],
    'OTM'          : ["Smart modulating Thermostat", 'Home+Control']
    }

# UNITS used by Netatmo services
UNITS = {
    "unit" : {
        0: "metric",
        1: "imperial"
    },
    "windunit" : {
        0: "kph",
        1: "mph",
        2: "ms",
        3: "beaufort",
        4: "knot"
    },
    "pressureunit" : {
        0: "mbar",
        1: "inHg",
        2: "mmHg"
    },
    "Health index" : {                                                                    # Homecoach
        0: "Healthy",
        1: "Fine",
        2: "Fair",
        3: "Poor",
        4: "Unhealthy"
    },
    "Wifi status" : {                                                                     # Wifi Signal quality
        86: "Bad",
        71: "Average",
        56: "Good"
    }
}

# Logger context
logger = logging.getLogger("lnetatmo")


class NoDevice( Exception ):
    pass


class NoHome( Exception ):
    pass


class AuthFailure( Exception ):
    pass


class outOfScope( Exception ):
    pass


class ClientAuth:
    """
    Request authentication and keep access token available through token method. Renew it automatically if necessary

    Args:
        clientId (str): Application clientId delivered by Netatmo on dev.netatmo.com
        clientSecret (str): Application Secret key delivered by Netatmo on dev.netatmo.com
        refreshToken (str) : Scoped refresh token
    """

    def __init__(self, clientId=None,
                       clientSecret=None,
                       refreshToken=None,
                       credentialFile=None):
        
        # replace values with content of env variables if defined
        clientId = getenv("CLIENT_ID", clientId)
        clientSecret = getenv("CLIENT_SECRET", clientSecret)
        refreshToken = getenv("REFRESH_TOKEN", refreshToken)

        # Look for credentials in file if not already provided
        # Note: this file will be rewritten by the library to record refresh_token change
        # If you run your application in container, remember to persist this file
        if not (clientId and clientSecret and refreshToken):
            credentialFile = credentialFile or expanduser("~/.netatmo.credentials")
            self._credentialFile = credentialFile
            with open(self._credentialFile, "r") as f:
                cred = {k.upper():v for k,v in json.loads(f.read()).items()}

        self._clientId = clientId or cred["CLIENT_ID"]
        self._clientSecret = clientSecret or cred["CLIENT_SECRET"]
        self.refreshToken = refreshToken or cred["REFRESH_TOKEN"]
        self.expiration = 0 # Force refresh token

    @property
    def accessToken(self):
        if self.expiration < time.time() : self.renew_token()
        return self._accessToken

    def renew_token(self):
        postParams = {
                "grant_type" : "refresh_token",
                "refresh_token" : self.refreshToken,
                "client_id" : self._clientId,
                "client_secret" : self._clientSecret
                }
        resp = postRequest("authentication", _AUTH_REQ, postParams)
        if self.refreshToken != resp['refresh_token']:
            self.refreshToken = resp['refresh_token']
            cred = {"CLIENT_ID":self._clientId,
                    "CLIENT_SECRET":self._clientSecret,
                    "REFRESH_TOKEN":self.refreshToken }
            if hasattr(type(self), "_credentialFile"):
                with open(self._credentialFile, "w") as f:
                    f.write(json.dumps(cred, indent=True))
        self._accessToken = resp['access_token']
        self.expiration = int(resp['expire_in'] + time.time())


class User:
    """
    This class returns basic information about the user

    Args:
        authData (ClientAuth): Authentication information with a working access Token
    """
    warnings.warn("The 'User' class is no longer maintained by Netatmo",
            DeprecationWarning )
    def __init__(self, authData):
        postParams = {
                "access_token" : authData.accessToken
                }
        resp = postRequest("Weather station", _GETSTATIONDATA_REQ, postParams)
        self.rawData = resp['body']
        self.devList = self.rawData['devices']
        self.ownerMail = self.rawData['user']['mail']


class UserInfo:
    """
    This class is populated with data from various Netatmo requests to provide
    complimentary data (eg Units for Weatherdata)
    """
    pass


class HomeStatus:
    """
    List all Home+Control devices (Smarther thermostat, Socket, Cable Output, Centralized fan, Micromodules, ......)

    Args:
        authData (clientAuth): Authentication information with a working access Token
        home : Home name or id of the home who's thermostat belongs to
    """
    def __init__(self, authData, home_id):

        self.getAuthToken = authData.accessToken
        postParams = {
                "access_token" : self.getAuthToken,
                "home_id": home_id
                }
        resp = postRequest("home_status", _HOME_STATUS, postParams)
        self.resp = resp
        self.rawData = resp['body']['home']
        if not self.rawData : raise NoHome("No home %s found" % home_id)
        self.rooms = self.rawData['rooms']
        self.modules = self.rawData['modules']

    def getRoomsId(self):
        return [room['id'] for room in self.rooms]

    def getListRoomParam(self, room_id):
        for room in self.rooms:
            if(room['id'] == room_id):
                return [param for param in room]
        return None

    def getRoomParam(self, room_id, param):
        for room in self.rooms:
            if(room['id'] == room_id and param in room):
                return room[param]
        return None

    def getModulesId(self):
        return [module['id'] for module in self.modules]

    def getListModuleParam(self, module_id):
        for module in self.modules:
            if(module['id'] == module_id):
                return [param for param in module]
        return None

    def getModuleParam(self, module_id, param):
        for module in self.modules:
            if(module['id'] == module_id and param in module):
                return module[param]
        return None


class ThermostatData:
    """
    List the Thermostat and temperature modules

    Args:
        authData (clientAuth): Authentication information with a working access Token
        home : Home name or id of the home who's thermostat belongs to
    """
    def __init__(self, authData, home=None):

        # I don't own a thermostat thus I am not able to test the Thermostat support
        warnings.warn("The Thermostat code is not tested due to the lack of test environment.\n" \
                      "As Netatmo is continuously breaking API compatibility, risk that current bindings are wrong is high.\n" \
                      "Please report found issues (https://github.com/philippelt/netatmo-api-python/issues)",
                       RuntimeWarning )

        self.getAuthToken = authData.accessToken
        postParams = {
                "access_token" : self.getAuthToken
                }
        resp = postRequest("Thermostat", _GETTHERMOSTATDATA_REQ, postParams)
        self.rawData = resp['body']['devices']
        if not self.rawData : raise NoDevice("No thermostat available")
        #
        # keeping OLD code for Reference
#        self.thermostatData = filter_home_data(self.rawData, home)
#        if not self.thermostatData : raise NoHome("No home %s found" % home)
#        self.thermostatData['name'] = self.thermostatData['home_name']                    # New key = 'station_name'
#        for m in self.thermostatData['modules']:
#            m['name'] = m['module_name']
#        self.defaultThermostat = self.thermostatData['home_name']                         # New key = 'station_name'
#        self.defaultThermostatId = self.thermostatData['_id']
#        self.defaultModule = self.thermostatData['modules'][0]
        # Standard the first Relaystation and Thermostat is returned
        # self.rawData is list all stations

    def Relay_Plug(self, _id=None):
        for Relay in self.rawData:
            if _id in Relay:
                return Relay
            else:
                #print (Relay['_id'])
                return Relay

    def Thermostat_Data(self):
        for thermostat in self.Relay_Plug()['modules']:
            #
            return thermostat
            
    def getThermostat(self, name=None, tid=None):
        if self.rawData[0]['station_name'] != name: return None                           # OLD ['name']
        else: return
        return self.thermostat[self.defaultThermostatId]

    def moduleNamesList(self, name=None, tid=None):
        thermostat = self.getThermostat(name=name, tid=tid)
        return [m['name'] for m in thermostat['modules']] if thermostat else None

    def getModuleByName(self, name, thermostatId=None):                                   # ERROR  'NoneType' object is not subscriptable
        thermostat = self.getThermostat(tid=thermostatId)
        for m in thermostat['modules']:
            if m['name'] == name: return m
        return None


class WeatherStationData:
    """
    List the Weather Station devices (stations and modules)

    Args:
        authData (ClientAuth): Authentication information with a working access Token
    """
    def __init__(self, authData, home=None, station=None):
        self.getAuthToken = authData.accessToken
        postParams = {
                "access_token" : self.getAuthToken
                }
        resp = postRequest("Weather station", _GETSTATIONDATA_REQ, postParams)
        self.rawData = resp['body']['devices']
        # Weather data
        if not self.rawData : raise NoDevice("No weather station in any homes")
        # Stations are no longer in the Netatmo API, keeping them for compatibility
        self.stations = { d['station_name'] : d for d in self.rawData }
        self.stationIds = { d['_id'] : d for d in self.rawData }
        self.homes = { d['home_name'] : d["station_name"] for d in self.rawData }
        # Keeping the old behavior for default station name
        if home and home not in self.homes : raise NoHome("No home with name %s" % home)
        self.default_home = home or list(self.homes.keys())[0]
        if station:
            if station not in self.stations:
                # May be a station_id convert it to corresponding station name
                s = self.stationById(station)
                if s :
                    station = s["station_name"]
                else:
                    raise NoDevice("No station with name or id %s" % station)
            self.default_station = station
        else:
            self.default_station =  [v["station_name"] for k,v in self.stations.items() if v["home_name"] == self.default_home][0]
        self.modules = dict()
        self.default_station_data = self.stationByName(self.default_station)
        if 'modules' in self.default_station_data:
            for m in self.default_station_data['modules']:
                self.modules[ m['_id'] ] = m
        # User data
        userData = resp['body']['user']
        self.user = UserInfo()
        setattr(self.user, "mail", userData['mail'])
        for k,v in userData['administrative'].items():
            if k in UNITS:
                setattr(self.user, k, UNITS[k][v])
            else:
                setattr(self.user, k, v)

    def modulesNamesList(self, station=None):
        s = self.getStation(station)
        if not s: raise NoDevice("No station with name or id %s" % station)
        self.default_station = station
        self.default_station_data = s
        self.modules = dict()
        if 'modules' in self.default_station_data:
            for m in self.default_station_data['modules']:
                self.modules[ m['_id'] ] = m
        res = [m['module_name'] for m in self.modules.values()]
        res.append(s['module_name'])
        return res

    # Both functions (byName and byStation) are here for historical reason,
    # considering that chances are low that a station name could be confused with a station ID,
    # there should be in fact a single function for getting station data

    def getStation(self, station=None):
        if not station : station = self.default_station
        if station in self.stations : return self.stations[station]
        if station in self.stationIds : return self.stationIds[station]
        return None

    def getModule(self, module):
        if module in self.modules: return self.modules[module]
        for m in self.modules.values():
            if m['module_name'] == module : return m
        return None
    
    # Functions for compatibility with previous versions
    def stationByName(self, station=None):
        return self.getStation(station)
    def stationById(self, sid):
        return self.getStation(sid)
    def moduleByName(self, module):
        return self.getModule(module)
    def moduleById(self, mid):
        return self.getModule(mid)

    def lastData(self, station=None, exclude=0):
        s = self.stationByName(station) or self.stationById(station)
        # Breaking change from Netatmo : dashboard_data no longer available if station lost
        if not s or 'dashboard_data' not in s : return None
        lastD = dict()
        # Define oldest acceptable sensor measure event
        limit = (time.time() - exclude) if exclude else 0
        ds = s['dashboard_data']
        if ds.get('time_utc',limit+10) > limit :
            lastD[s['module_name']] = ds.copy()
            lastD[s['module_name']]['When'] = lastD[s['module_name']].pop("time_utc") if 'time_utc' in lastD[s['module_name']] else time.time()
            lastD[s['module_name']]['wifi_status'] = s['wifi_status']
        if 'modules' in s:
            for module in s["modules"]:
                # Skip lost modules that no longer have dashboard data available
                if 'dashboard_data' not in module : continue
                ds = module['dashboard_data']
                if ds.get('time_utc',limit+10) > limit :
                    # If no module_name has been setup, use _id by default
                    if "module_name" not in module : module['module_name'] = module["_id"]
                    lastD[module['module_name']] = ds.copy()
                    lastD[module['module_name']]['When'] = lastD[module['module_name']].pop("time_utc") if 'time_utc' in lastD[module['module_name']] else time.time()
                    # For potential use, add battery and radio coverage information to module data if present
                    for i in ('battery_vp', 'battery_percent', 'rf_status') :
                        if i in module : lastD[module['module_name']][i] = module[i]
        return lastD

    def checkNotUpdated(self, delay=3600):
        res = self.lastData()
        ret = []
        for mn,v in res.items():
            if time.time()-v['When'] > delay : ret.append(mn)
        return ret if ret else None

    def checkUpdated(self, delay=3600):
        res = self.lastData()
        ret = []
        for mn,v in res.items():
            if time.time()-v['When'] < delay : ret.append(mn)
        return ret if ret else None

    def getMeasure(self, device_id, scale, mtype, module_id=None, date_begin=None, date_end=None, limit=None, optimize=False, real_time=False):
        postParams = { "access_token" : self.getAuthToken }
        postParams['device_id']  = device_id
        if module_id : postParams['module_id'] = module_id
        postParams['scale']      = scale
        postParams['type']       = mtype
        if date_begin : postParams['date_begin'] = date_begin
        if date_end : postParams['date_end'] = date_end
        if limit : postParams['limit'] = limit
        postParams['optimize'] = "true" if optimize else "false"
        postParams['real_time'] = "true" if real_time else "false"
        return postRequest("Weather station", _GETMEASURE_REQ, postParams)

    def MinMaxTH(self, module=None, frame="last24"):
        s = self.default_station_data
        if frame == "last24":
            end = time.time()
            start = end - 24*3600 # 24 hours ago
        elif frame == "day":
            start, end = todayStamps()
        if module and module != s['module_name']:
            m = self.moduleById(module) or self.moduleByName(module)
            if not m : raise NoDevice("Can't find module %s" % module)
            # retrieve module's data
            resp = self.getMeasure(
                    device_id  = s['_id'],
                    module_id  = m['_id'],
                    scale      = "max",
                    mtype      = "Temperature,Humidity",
                    date_begin = start,
                    date_end   = end)
        else : # retrieve station's data
            resp = self.getMeasure(
                    device_id  = s['_id'],
                    scale      = "max",
                    mtype      = "Temperature,Humidity",
                    date_begin = start,
                    date_end   = end)
        if resp and resp['body']:
            T = [v[0] for v in resp['body'].values()]
            H = [v[1] for v in resp['body'].values()]
            return min(T), max(T), min(H), max(H)
        else:
            return None


class DeviceList(WeatherStationData):
    """
    This class is now deprecated. Use WeatherStationData directly instead
    """
    warnings.warn("The 'DeviceList' class was renamed 'WeatherStationData'",
            DeprecationWarning )
    pass


class HomeData:
    """
    List the Netatmo home informations (Homes, cameras, events, persons)

    Args:
        authData (ClientAuth): Authentication information with a working access Token
    """
    def __init__(self, authData, home=None):
        self.getAuthToken = authData.accessToken
        postParams = {
            "access_token" : self.getAuthToken
            }
        resp = postRequest("Home data", _GETHOMEDATA_REQ, postParams)
        self.rawData = resp['body']
        # Collect homes
        self.homes = { d['id'] : d for d in self.rawData['homes'] }
        for k, v in self.homes.items():
            self.homeid = k
            C = v.get('cameras')
            P = v.get('persons')
            S = v.get('smokedetectors')
            E = v.get('events')
            if not S:
                logger.warning('No Smokedetectors found')
#                raise NoDevice("No Devices available")
            if not C:
                logger.warning('No Cameras found')
#                raise NoDevice("No Cameras available")
            if not P:
                logger.warning('No Persons found')
#                raise NoDevice("No Persons available")
            if not E:
                logger.warning('No events found')
#                raise NoDevice("No Events available")
        if S or C or P or E:
            self.default_home = home or list(self.homes.values())[0]['name']
            # Split homes data by category
            self.persons = dict()
            self.events = dict()
            self.cameras = dict()
            self.lastEvent = dict()
            for i in range(len(self.rawData['homes'])):
                curHome = self.rawData['homes'][i]
                nameHome = curHome['name']
                if nameHome not in self.cameras:
                    self.cameras[nameHome] = dict()
                if 'persons' in curHome:
                    for p in curHome['persons']:
                        self.persons[ p['id'] ] = p
                if 'events' in curHome:
                    for e in curHome['events']:
                        if e['camera_id'] not in self.events:
                            self.events[ e['camera_id'] ] = dict()
                        self.events[ e['camera_id'] ][ e['time'] ] = e
                if 'cameras' in curHome:
                    for c in curHome['cameras']:
                        self.cameras[nameHome][ c['id'] ] = c
                        c["home_id"] = curHome['id']
            for camera in self.events:
                self.lastEvent[camera] = self.events[camera][sorted(self.events[camera])[-1]]
            if not self.cameras[self.default_home] : raise NoDevice("No camera available in default home")
            self.default_camera = list(self.cameras[self.default_home].values())[0]
        else:
            pass
#            raise NoDevice("No Devices available")
    
    def homeById(self, hid):
        return None if hid not in self.homes else self.homes[hid]

    def homeByName(self, home=None):
        if not home: home = self.default_home
        for key,value in self.homes.items():
            if value['name'] == home:
                return self.homes[key]

    def cameraById(self, cid):
        for home,cam in self.cameras.items():
            if cid in self.cameras[home]:
                return self.cameras[home][cid]
        return None

    def cameraByName(self, camera=None, home=None):
        if not camera and not home:
            return self.default_camera
        elif home and camera:
            if home not in self.cameras:
                return None
            for cam_id in self.cameras[home]:
                if self.cameras[home][cam_id]['name'] == camera:
                    return self.cameras[home][cam_id]
        elif not home and camera:
            for home, cam_ids in self.cameras.items():
                for cam_id in cam_ids:
                    if self.cameras[home][cam_id]['name'] == camera:
                        return self.cameras[home][cam_id]
        else:
            return list(self.cameras[home].values())[0]
        return None

    def cameraUrls(self, camera=None, home=None, cid=None):
        """
        Return the vpn_url and the local_url (if available) of a given camera
        in order to access to its live feed
        Can't use the is_local property which is mostly false in case of operator
        dynamic IP change after presence start sequence
        """
        local_url = None
        vpn_url = None
        if cid:
            camera_data=self.cameraById(cid)
        else:
            camera_data=self.cameraByName(camera=camera, home=home)
        if camera_data:
            vpn_url = camera_data['vpn_url']
            resp = postRequest("Camera", vpn_url + '/command/ping')
            temp_local_url=resp['local_url']
            try:
                resp = postRequest("Camera", temp_local_url + '/command/ping',timeout=1)
                if resp and temp_local_url == resp['local_url']:
                    local_url = temp_local_url
            except:  # On this particular request, vithout errors from previous requests, error is timeout
                local_url = None
        return vpn_url, local_url

    def url(self, camera=None, home=None, cid=None):
        vpn_url, local_url = self.cameraUrls(camera, home, cid)
        # Return local if available else vpn
        return local_url or vpn_url

    def personsAtHome(self, home=None):
        """
        Return the list of known persons who are currently at home
        """
        if not home: home = self.default_home
        home_data = self.homeByName(home)
        atHome = []
        for p in home_data['persons']:
            #Only check known persons
            if 'pseudo' in p:
                if not p["out_of_sight"]:
                    atHome.append(p['pseudo'])
        return atHome

    def getCameraPicture(self, image_id, key):
        """
        Download a specific image (of an event or user face) from the camera
        """
        postParams = {
            "access_token" : self.getAuthToken,
            "image_id" : image_id,
            "key" : key
            }
        resp = postRequest("Camera", _GETCAMERAPICTURE_REQ, postParams)
        image_type = imghdr.what('NONE.FILE',resp)
        return resp, image_type

    def getProfileImage(self, name):
        """
        Retrieve the face of a given person
        """
        for p in self.persons:
            if 'pseudo' in self.persons[p]:
                if name == self.persons[p]['pseudo']:
                    image_id = self.persons[p]['face']['id']
                    key = self.persons[p]['face']['key']
                    return self.getCameraPicture(image_id, key)
        return None, None

    def updateEvent(self, event=None, home=None):
        """
        Update the list of event with the latest ones
        """
        if not home: home=self.default_home
        if not event:
            #If not event is provided we need to retrieve the oldest of the last event seen by each camera
            listEvent = dict()
            for cam_id in self.lastEvent:
                listEvent[self.lastEvent[cam_id]['time']] = self.lastEvent[cam_id]
            event = listEvent[sorted(listEvent)[0]]

        home_data = self.homeByName(home)
        postParams = {
            "access_token" : self.getAuthToken,
            "home_id" : home_data['id'],
            "event_id" : event['id']
        }
        resp = postRequest("Camera", _GETEVENTSUNTIL_REQ, postParams)
        eventList = resp['body']['events_list']
        for e in eventList:
            self.events[ e['camera_id'] ][ e['time'] ] = e
        for camera in self.events:
            self.lastEvent[camera]=self.events[camera][sorted(self.events[camera])[-1]]

    def personSeenByCamera(self, name, home=None, camera=None):
        """
        Return True if a specific person has been seen by a camera
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            logger.warning("personSeenByCamera: Camera name or home is unknown")
            return False
        #Check in the last event is someone known has been seen
        if self.lastEvent[cam_id]['type'] == 'person':
            person_id = self.lastEvent[cam_id]['person_id']
            if 'pseudo' in self.persons[person_id]:
                if self.persons[person_id]['pseudo'] == name:
                    return True
        return False

    def _knownPersons(self):
        known_persons = dict()
        for p_id,p in self.persons.items():
            if 'pseudo' in p:
                known_persons[ p_id ] = p
        return known_persons

    def someoneKnownSeen(self, home=None, camera=None):
        """
        Return True if someone known has been seen
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            logger.warning("personSeenByCamera: Camera name or home is unknown")
            return False
        #Check in the last event is someone known has been seen
        if self.lastEvent[cam_id]['type'] == 'person':
            if self.lastEvent[cam_id]['person_id'] in self._knownPersons():
                return True
        return False

    def someoneUnknownSeen(self, home=None, camera=None):
        """
        Return True if someone unknown has been seen
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            logger.warning("personSeenByCamera: Camera name or home is unknown")
            return False
        #Check in the last event is someone known has been seen
        if self.lastEvent[cam_id]['type'] == 'person':
            if self.lastEvent[cam_id]['person_id'] not in self._knownPersons():
                return True
        return False

    def motionDetected(self, home=None, camera=None):
        """
        Return True if movement has been detected
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            logger.warning("personSeenByCamera: Camera name or home is unknown")
            return False
        if self.lastEvent[cam_id]['type'] == 'movement':
            return True
        return False

    def presenceUrl(self, camera=None, home=None, cid=None, setting=None):
        camera = self.cameraByName(home=home, camera=camera) or self.cameraById(cid=cid)
        if camera["type"] != "NOC": return None # Not a presence camera
        vpnUrl, localUrl = self.cameraUrls(cid=camera["id"])
        return localUrl

    def presenceLight(self, camera=None, home=None, cid=None, setting=None):
        url = self.presenceUrl(home=home, camera=camera) or self.cameraById(cid=cid)
        if not url or setting not in ("on", "off", "auto"): return None
        if setting : return "Currently unsupported"
        return cameraCommand(url, _PRES_CDE_GET_LIGHT)["mode"]
        # Not yet supported
        #if not setting: return cameraCommand(url, _PRES_CDE_GET_LIGHT)["mode"]
        #else: return cameraCommand(url, _PRES_CDE_SET_LIGHT, setting)

    def presenceStatus(self, mode, camera=None, home=None, cid=None):
        url = self.presenceUrl(home=home, camera=camera) or self.cameraById(cid=cid)
        if not url or mode not in ("on", "off") : return None
        r = cameraCommand(url, _CAM_CHANGE_STATUS, mode)
        return mode if r["status"] == "ok" else None

    def presenceSetAction(self, camera=None, home=None, cid=None,
                          eventType=_PRES_DETECTION_KIND[0], action=2):
        return "Currently unsupported"
        if eventType not in _PRES_DETECTION_KIND or \
           action not in _PRES_DETECTION_SETUP : return None
        camera = self.cameraByName(home=home, camera=camera) or self.cameraById(cid=cid)
        postParams = { "access_token" : self.getAuthToken,
                       "home_id" : camera["home_id"],
                       "presence_settings[presence_record_%s]" % eventType : _PRES_DETECTION_SETUP.index(action)
                     }
        resp = postRequest("Camera", _POST_UPDATE_HOME_REQ, postParams)
        self.rawData = resp['body']

    def getLiveSnapshot(self, camera=None, home=None, cid=None):
        camera = self.cameraByName(home=home, camera=camera) or self.cameraById(cid=cid)
        vpnUrl, localUrl = self.cameraUrls(cid=camera["id"])
        url = localUrl or vpnUrl
        return cameraCommand(url, _PRES_CDE_GET_SNAP)


class WelcomeData(HomeData):
    """
    This class is now deprecated. Use HomeData instead
    Home can handle many devices, not only Welcome cameras
    """
    warnings.warn("The 'WelcomeData' class was renamed 'HomeData' to handle new Netatmo Home capabilities",
            DeprecationWarning )
    pass


class HomesData:
    """
    List the Netatmo actual topology and static information of all devices present
    into a user account. It is also possible to specify a home_id to focus on one home.

    Args:
        authData (clientAuth): Authentication information with a working access Token
        home : Home name or id of the home who's module belongs to
    """
    def __init__(self, authData, home=None):
        #
        self.getAuthToken = authData.accessToken
        postParams = {
                "access_token" : self.getAuthToken,
                "home_id": home
                }
        #
        resp = postRequest("Module", _GETHOMES_DATA, postParams)
#        self.rawData = resp['body']['devices']
        self.rawData = resp['body']['homes']
        if not self.rawData : raise NoHome("No home %s found" % home)
        #
        if home:
            # Find a home who's home id or name is the one requested
            for h in self.rawData:
                #print (h.keys())
                if h["name"] == home or h["id"] == home:
                   self.Homes_Data = h
#        print (self.Homes_Data)
        if not self.Homes_Data : raise NoDevice("No Devices available")


class HomeCoach:
    """
    List the HomeCoach modules
        
    Args:
        authData (clientAuth): Authentication information with a working access Token
        home : Home name or id of the home who's HomeCoach belongs to
    """
    def __init__(self, authData, home=None):
        # I don't own a HomeCoach thus I am not able to test the HomeCoach support
        
#        warnings.warn("The HomeCoach code is not tested due to the lack of test environment.\n",  RuntimeWarning )
#                      "As Netatmo is continuously breaking API compatibility, risk that current bindings are wrong is high.\n" \
#                      "Please report found issues (https://github.com/philippelt/netatmo-api-python/issues)"

        self.getAuthToken = authData.accessToken
        postParams = {
                "access_token" : self.getAuthToken
                }
        resp = postRequest("HomeCoach", _GETHOMECOACH, postParams)
        self.rawData = resp['body']['devices']
        # homecoach data
        if not self.rawData : raise NoDevice("No HomeCoach available")

        for i in range(len(self.rawData)):
            #
            self.HomecoachDevice = self.rawData[i]
#           print ('Homecoach = ', self.HomecoachDevice)
#           print (' ')
#           print ('Homecoach_data = ', self.rawData[i]['dashboard_data'])
#           print (' ')

    def Dashboard(self):
        D = self.HomecoachDevice['dashboard_data']
        return D

    def lastData(self, id=None, exclude=0):
        if id is not None:
                s = self.HomecoachDevice['dashboard_data']['time_utc']
                _id = self.HomecoachDevice['_id']
                return {'When':s}, {'_id':_id}
        else:
            return {'When': 0 }, {'_id': id}

    def checkNotUpdated(self, res, _id, delay=3600):
        ret = []
        if time.time()-res['When'] > delay : ret.append({_id: 'Device Not Updated'})
        return ret if ret else None

    def checkUpdated(self, res, _id, delay=3600):
        ret = []
        if time.time()-res['When'] < delay : ret.append({_id: 'Device up-to-date'})
        return ret if ret else None


# Utilities routines

def rawAPI(authData, url, parameters={}):
    fullUrl = _BASE_URL + "api/" + url
    parameters["access_token"] = authData.accessToken
    resp = postRequest("rawAPI", fullUrl, parameters)
    return resp["body"] if "body" in resp else None

def filter_home_data(rawData, home):
    if home:
        # Find a home who's home id or name is the one requested
        for h in rawData:
            if h["home_name"] == home or h["home_id"] == home:
                return h
        return None
    # By default, the first home is returned
    return rawData[0]

def cameraCommand(cameraUrl, commande, parameters=None, timeout=3):
    url = cameraUrl + ( commande % parameters if parameters else commande)
    return postRequest("Camera", url, timeout=timeout)

def postRequest(topic, url, params=None, timeout=10):
    if PYTHON3:
        req = urllib.request.Request(url)
        if params:
            req.add_header("Content-Type","application/x-www-form-urlencoded;charset=utf-8")
            if "access_token" in params:
                req.add_header("Authorization","Bearer %s" % params.pop("access_token"))
            params = urllib.parse.urlencode(params).encode('utf-8')
        try:
            resp = urllib.request.urlopen(req, params, timeout=timeout) if params else urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as err:
            if err.code == 403:
                logger.warning("Your current token scope do not allow access to %s" % topic)
            else:
                logger.error("code=%s, reason=%s, body=%s" % (err.code, err.reason, err.fp.read()))
            return None
    else:
        if params:
            token = params.pop("access_token") if "access_token" in params else None
            params = urlencode(params)
            headers = {"Content-Type"  : "application/x-www-form-urlencoded;charset=utf-8"}
            if token: headers["Authorization"] = "Bearer %s" % token
        req = urllib2.Request(url=url, data=params, headers=headers) if params else urllib2.Request(url=url, headers=headers)
        try:
            resp = urllib2.urlopen(req, timeout=timeout)
        except urllib2.HTTPError as err:
            if err.code == 403:
                logger.warning("Your current token scope do not allow access to %s" % topic)
            else:
                logger.error("code=%s, reason=%s" % (err.code, err.reason))
            return None
    data = b""
    for buff in iter(lambda: resp.read(65535), b''): data += buff
    # Return values in bytes if not json data to handle properly camera images
    returnedContentType = resp.getheader("Content-Type") if PYTHON3 else resp.info()["Content-Type"]
    return json.loads(data.decode("utf-8")) if "application/json" in returnedContentType else data

def toTimeString(value):
    return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(int(value)))

def toEpoch(value):
    return int(time.mktime(time.strptime(value,"%Y-%m-%d_%H:%M:%S")))

def todayStamps():
    today = time.strftime("%Y-%m-%d")
    today = int(time.mktime(time.strptime(today,"%Y-%m-%d")))
    return today, today+3600*24

# Global shortcut

def getStationMinMaxTH(station=None, module=None, home=None):
    authorization = ClientAuth()
    devList = WeatherStationData(authorization, station=station, home=home)
    if module == "*":
        pass
    elif module:
        module = devList.moduleById(module) or devList.moduleByName(module)
        if not module: raise NoDevice("No such module %s" % module)
        else: module = module["module_name"]
    else:
        module = list(devList.modules.values())[0]["module_name"]
    lastD = devList.lastData()
    if module == "*":
        result = dict()
        for m in lastD.keys():
            if time.time()-lastD[m]['When'] > 3600 : continue
            r = devList.MinMaxTH(module=m)
            if r:
                result[m] = (r[0], lastD[m]['Temperature'], r[1])
    else:
        if time.time()-lastD[module]['When'] > 3600 : result = ["-", "-"]
        else :
            result = [lastD[module]['Temperature'], lastD[module]['Humidity']]
            result.extend(devList.MinMaxTH(module))
    return result


# auto-test when executed directly

if __name__ == "__main__":

    from sys import exit, stdout, stderr

    logging.basicConfig(format='%(name)s - %(levelname)s: %(message)s', level=logging.INFO)

    authorization = ClientAuth()                                                          # Test authentication method

    try:
        weatherStation = WeatherStationData(authorization)                                # Test DEVICELIST
    except NoDevice:
        logger.warning("No weather station available for testing")
    else:
        weatherStation.MinMaxTH()                                                         # Test GETMEASUR

    try:
        homes = HomeData(authorization)
        homeid = homes.homeid
    except NoDevice :
        logger.warning("No home available for testing")

    try:
        thermostat = ThermostatData(authorization)
        Default_relay = thermostat.Relay_Plug()
        Default_thermostat = thermostat.Thermostat_Data()
    except NoDevice:
        logger.warning("No thermostat avaible for testing")

    try:
#        homesdata = lnetatmo.HomesData(authorization)
# ERROR ; Your current token scope do not allow access to Module ?  - No Home ID given !
        homesdata = HomesData(authorization, homeid)
    except NoDevice:
        logger.warning("No HomesData avaible for testing")
            
    try:
        Homecoach = HomeCoach(authorization)
    except NoDevice:
        logger.warning("No HomeCoach avaible for testing")
        
    # If we reach this line, all is OK
    logger.info("OK")

    exit(0)
