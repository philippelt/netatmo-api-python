# Published Jan 2013
# Revised Jan 2014 (to add new modules data)
# Revised 2016 (to add camera support)
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
from sys import version_info
from os import getenv
from os.path import expanduser, exists
import json, time
import imghdr
import warnings

# HTTP libraries depends upon Python 2 or 3
if version_info.major == 3 :
    import urllib.parse, urllib.request
else:
    from urllib import urlencode
    import urllib2

######################## AUTHENTICATION INFORMATION ######################

# To be able to have a program accessing your netatmo data, you have to register your program as
# a Netatmo app in your Netatmo account. All you have to do is to give it a name (whatever) and you will be
# returned a client_id and secret that your app has to supply to access netatmo servers.

# To ease Docker packaging of your application, you can setup your authentication parameters through env variables

# Authentication use :
#  1 - Values hard coded in the library
#  2 - The .netatmo.credentials file in JSON format in your home directory
#  3 - Values defined in environment variables : CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD

# Each level override values defined in the previous level. You could define CLIENT_ID and CLIENT_SECRET hard coded in the library
# and username/password in .netatmo.credentials or environment variables

cred = {                       # You can hard code authentication information in the following lines
        "CLIENT_ID" :  "",     #   Your client ID from Netatmo app registration at http://dev.netatmo.com/dev/listapps
        "CLIENT_SECRET" : "",  #   Your client app secret   '     '
        "USERNAME" : "",       #   Your netatmo account username
        "PASSWORD" : ""        #   Your netatmo account password
        }

# Other authentication setup management (optionals)

CREDENTIALS = expanduser("~/.netatmo.credentials")

def getParameter(key, default):
    return getenv(key, default[key])

# 2 : Override hard coded values with credentials file if any
if exists(CREDENTIALS) :
    with open(CREDENTIALS, "r") as f:
        cred.update({k.upper():v for k,v in json.loads(f.read()).items()})

# 3 : Override final value with content of env variables if defined
_CLIENT_ID     = getParameter("CLIENT_ID", cred)
_CLIENT_SECRET = getParameter("CLIENT_SECRET", cred)
_USERNAME      = getParameter("USERNAME", cred)
_PASSWORD      = getParameter("PASSWORD", cred)

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


#TODO# Undocumented (but would be very usefull) API : Access currently forbidden (403)

# _POST_UPDATE_HOME_REQ  = _BASE_URL + "/api/updatehome"

# For presence setting (POST BODY):
# _PRES_BODY_REC_SET     = "home_id=%s&presence_settings[presence_record_%s]=%s"   # (HomeId, DetectionKind, DetectionSetup.index)
_PRES_DETECTION_KIND   = ("humans", "animals", "vehicles", "movements")
_PRES_DETECTION_SETUP  = ("ignore", "record", "record & notify")

# _PRES_BODY_ALERT_TIME  = "home_id=%s&presence_settings[presence_notify_%s]=%s"   # (HomeID, "from"|"to", "hh:mm")

# Regular (documented) commands (both cameras)

_PRES_CDE_GET_SNAP     = "/live/snapshot_720.jpg"

#TODO# Undocumented (taken from https://github.com/KiboOst/php-NetatmoCameraAPI/blob/master/class/NetatmoCameraAPI.php)
# Work with local_url only (undocumented scope control probably)

# For Presence camera

_PRES_CDE_GET_LIGHT    = "/command/floodlight_get_config"
# Not working yet, probably due to scope restriction
#_PRES_CDE_SET_LIGHT    = "/command/floodlight_set_config?config=mode:%s"    # "auto"|"on"|"off"


# For all cameras

_CAM_CHANGE_STATUS     = "/command/changestatus?status=%s"            # "on"|"off"
# Not working yet
#_CAM_FTP_ACTIVE        = "/command/ftp_set_config?config=on_off:%s"   # "on"|"off"


class NoDevice( Exception ):
    pass


class AuthFailure( Exception ):
    pass


class ClientAuth:
    """
    Request authentication and keep access token available through token method. Renew it automatically if necessary

    Args:
        clientId (str): Application clientId delivered by Netatmo on dev.netatmo.com
        clientSecret (str): Application Secret key delivered by Netatmo on dev.netatmo.com
        username (str)
        password (str)
        scope (Optional[str]): Default value is 'read_station'
            read_station: to retrieve weather station data (Getstationsdata, Getmeasure)
            read_camera: to retrieve Welcome data (Gethomedata, Getcamerapicture)
            access_camera: to access the camera, the videos and the live stream.
            Several value can be used at the same time, ie: 'read_station read_camera'
    """

    def __init__(self, clientId=_CLIENT_ID,
                       clientSecret=_CLIENT_SECRET,
                       username=_USERNAME,
                       password=_PASSWORD,
                       scope="read_station read_camera access_camera write_camera " \
                                 "read_presence access_presence write_presence read_thermostat write_thermostat"):
        
        postParams = {
                "grant_type" : "password",
                "client_id" : clientId,
                "client_secret" : clientSecret,
                "username" : username,
                "password" : password,
                "scope" : scope
                }
        resp = postRequest(_AUTH_REQ, postParams)
        if not resp: raise AuthFailure("Authentication request rejected")

        self._clientId = clientId
        self._clientSecret = clientSecret
        self._accessToken = resp['access_token']
        self.refreshToken = resp['refresh_token']
        self._scope = resp['scope']
        self.expiration = int(resp['expire_in'] + time.time())

    @property
    def accessToken(self):

        if self.expiration < time.time(): # Token should be renewed
            postParams = {
                    "grant_type" : "refresh_token",
                    "refresh_token" : self.refreshToken,
                    "client_id" : self._clientId,
                    "client_secret" : self._clientSecret
                    }
            resp = postRequest(_AUTH_REQ, postParams)
            self._accessToken = resp['access_token']
            self.refreshToken = resp['refresh_token']
            self.expiration = int(resp['expire_in'] + time.time())
        return self._accessToken


class User:
    """
    This class returns basic information about the user

    Args:
        authData (ClientAuth): Authentication information with a working access Token
    """
    def __init__(self, authData):
        postParams = {
                "access_token" : authData.accessToken
                }
        resp = postRequest(_GETSTATIONDATA_REQ, postParams)
        self.rawData = resp['body']
        self.devList = self.rawData['devices']
        self.ownerMail = self.rawData['user']['mail']


class ThermostatData:
    """
    List the Thermostat and temperature modules

    Args:
        authData (clientAuth): Authentication information with a working access Token
    """
    def __init__(self, authData):
        self.getAuthToken = authData.accessToken
        postParams = {
                "access_token" : self.getAuthToken
                }
        resp = postRequest(_GETTHERMOSTATDATA_REQ, postParams)
        self.rawData = resp['body']['devices']
        if not self.rawData : raise NoDevice("No thermostat available")
        self.thermostat = { d['_id'] : d for d in self.rawData }
        for t,v in self.thermostat.items():
            v['name'] = v['station_name']
            for m in v['modules']:
                m['name'] = m['module_name']
        self.defaultThermostat = self.rawData[0]['station_name']
        self.defaultThermostatId = self.rawData[0]['_id']
        self.defaultModule = self.rawData[0]['modules'][0]

    def getThermostat(self, name=None, tid=None):
        if tid:
            if tid in self.thermostat.keys():
                return self.thermostat[tid]
            else:
                return None
        elif name:
            for t in self.thermostat.values():
                if t['name'] == name: return t
            return None
        return self.thermostat[self.defaultThermostatId]

    def moduleNamesList(self, name=None, tid=None):
        thermostat = self.getThermostat(name=name, tid=tid)
        return [m['name'] for m in thermostat['modules']] if thermostat else None

    def getModuleByName(self, name, thermostatId=None):
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
    def __init__(self, authData):
        self.getAuthToken = authData.accessToken
        postParams = {
                "access_token" : self.getAuthToken
                }
        resp = postRequest(_GETSTATIONDATA_REQ, postParams)
        self.rawData = resp['body']['devices']
        if not self.rawData : raise NoDevice("No weather station available")
        self.stations = { d['_id'] : d for d in self.rawData }
        self.modules = dict()
        for i in range(len(self.rawData)):
            for m in self.rawData[i]['modules']:
                self.modules[ m['_id'] ] = m
        self.default_station = list(self.stations.values())[0]['station_name']

    def modulesNamesList(self, station=None):
        res = [m['module_name'] for m in self.modules.values()]
        res.append(self.stationByName(station)['module_name'])
        return res

    def stationByName(self, station=None):
        if not station : station = self.default_station
        for i,s in self.stations.items():
            if s['station_name'] == station :
                return self.stations[i]
        return None

    def stationById(self, sid):
        return None if sid not in self.stations else self.stations[sid]

    def moduleByName(self, module, station=None):
        s = None
        if station :
            s = self.stationByName(station)
            if not s : return None
        for m in self.modules:
            mod = self.modules[m]
            if mod['module_name'] == module :
                return mod
        return None

    def moduleById(self, mid, sid=None):
        s = self.stationById(sid) if sid else None
        if mid in self.modules :
            if s:
                for module in s['modules']:
                    if module['_id'] == mid:
                        return module
            else:
                return self.modules[mid]

    def lastData(self, station=None, exclude=0):
        s = self.stationByName(station) or self.stationById(station)
        if not s : return None
        lastD = dict()
        # Define oldest acceptable sensor measure event
        limit = (time.time() - exclude) if exclude else 0
        ds = s['dashboard_data']
        if ds['time_utc'] > limit :
            lastD[s['module_name']] = ds.copy()
            lastD[s['module_name']]['When'] = lastD[s['module_name']].pop("time_utc")
            lastD[s['module_name']]['wifi_status'] = s['wifi_status']
        for module in s["modules"]:
            ds = module['dashboard_data']
            if 'time_utc' not in ds:
                return None
            if ds['time_utc'] > limit :
                # If no module_name has been setup, use _id by default
                if "module_name" not in module : module['module_name'] = module["_id"]
                lastD[module['module_name']] = ds.copy()
                lastD[module['module_name']]['When'] = lastD[module['module_name']].pop("time_utc")
                # For potential use, add battery and radio coverage information to module data if present
                for i in ('battery_vp', 'rf_status') :
                    if i in module : lastD[module['module_name']][i] = module[i]
        return lastD

    def checkNotUpdated(self, station=None, delay=3600):
        res = self.lastData(station)
        ret = []
        for mn,v in res.items():
            if time.time()-v['When'] > delay : ret.append(mn)
        return ret if ret else None

    def checkUpdated(self, station=None, delay=3600):
        res = self.lastData(station)
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
        return postRequest(_GETMEASURE_REQ, postParams)

    def MinMaxTH(self, station=None, module=None, frame="last24"):
        if not station : station = self.default_station
        s = self.stationByName(station)
        if not s :
            s = self.stationById(station)
            if not s : return None
        if frame == "last24":
            end = time.time()
            start = end - 24*3600 # 24 hours ago
        elif frame == "day":
            start, end = todayStamps()
        if module and module != s['module_name']:
            m = self.moduleByName(module, s['station_name'])
            if not m :
                m = self.moduleById(s['_id'], module)
                if not m : return None
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
        if resp:
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
    def __init__(self, authData):
        self.getAuthToken = authData.accessToken
        postParams = {
            "access_token" : self.getAuthToken
            }
        resp = postRequest(_GETHOMEDATA_REQ, postParams)
        self.rawData = resp['body']
        # Collect homes
        self.homes = { d['id'] : d for d in self.rawData['homes'] }
        if not self.homes : raise NoDevice("No home available")
        self.default_home = list(self.homes.values())[0]['name']
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
            for p in curHome['persons']:
                self.persons[ p['id'] ] = p
            for e in curHome['events']:
                if e['camera_id'] not in self.events:
                    self.events[ e['camera_id'] ] = dict()
                self.events[ e['camera_id'] ][ e['time'] ] = e
            for c in curHome['cameras']:
                self.cameras[nameHome][ c['id'] ] = c
                c["home_id"] = curHome['id']
        for camera in self.events:
            self.lastEvent[camera] = self.events[camera][sorted(self.events[camera])[-1]]
        if not self.cameras[self.default_home] : raise NoDevice("No camera available in default home")
        self.default_camera = list(self.cameras[self.default_home].values())[0]

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
            resp = postRequest(vpn_url + '/command/ping')
            temp_local_url=resp['local_url']
            resp = postRequest(temp_local_url + '/command/ping',timeout=1)
            if resp and temp_local_url == resp['local_url']:
                local_url = temp_local_url
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
        resp = postRequest(_GETCAMERAPICTURE_REQ, postParams)
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
        resp = postRequest(_GETEVENTSUNTIL_REQ, postParams)
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
            print("personSeenByCamera: Camera name or home is unknown")
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
            print("personSeenByCamera: Camera name or home is unknown")
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
            print("personSeenByCamera: Camera name or home is unknown")
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
            print("personSeenByCamera: Camera name or home is unknown")
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
        resp = postRequest(_POST_UPDATE_HOME_REQ, postParams)
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

# Utilities routines

def cameraCommand(cameraUrl, commande, parameters=None, timeout=3):
    url = cameraUrl + ( commande % parameters if parameters else commande)
    return postRequest(url, timeout=timeout)
    
def postRequest(url, params=None, timeout=10):
    if version_info.major == 3:
        req = urllib.request.Request(url)
        if params:
            req.add_header("Content-Type","application/x-www-form-urlencoded;charset=utf-8")
            params = urllib.parse.urlencode(params).encode('utf-8')
        try:
            resp = urllib.request.urlopen(req, params, timeout=timeout) if params else urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.URLError:
            return None
    else:
        if params:
            params = urlencode(params)
            headers = {"Content-Type" : "application/x-www-form-urlencoded;charset=utf-8"}
        req = urllib2.Request(url=url, data=params, headers=headers) if params else urllib2.Request(url)
        try:
            resp = urllib2.urlopen(req, timeout=timeout)
        except urllib2.URLError:
            return None
    data = b""
    for buff in iter(lambda: resp.read(65535), b''): data += buff
    # Return values in bytes if not json data to handle properly camera images
    returnedContentType = resp.getheader("Content-Type") if version_info.major == 3 else resp.info()["Content-Type"]
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

def getStationMinMaxTH(station=None, module=None):
    authorization = ClientAuth()
    devList = DeviceList(authorization)
    if not station : station = devList.default_station
    if module :
        mname = module
    else :
        mname = devList.stationByName(station)['module_name']
    lastD = devList.lastData(station)
    if mname == "*":
        result = dict()
        for m in lastD.keys():
            if time.time()-lastD[m]['When'] > 3600 : continue
            r = devList.MinMaxTH(module=m)
            result[m] = (r[0], lastD[m]['Temperature'], r[1])
    else:
        if time.time()-lastD[mname]['When'] > 3600 : result = ["-", "-"]
        else : result = [lastD[mname]['Temperature'], lastD[mname]['Humidity']]
        result.extend(devList.MinMaxTH(station, mname))
    return result


# auto-test when executed directly

if __name__ == "__main__":

    from sys import exit, stdout, stderr

    if not _CLIENT_ID or not _CLIENT_SECRET or not _USERNAME or not _PASSWORD :
           stderr.write("Library source missing identification arguments to check lnetatmo.py (user/password/etc...)")
           exit(1)

    authorization = ClientAuth()  # Test authentication method
    
    try:
        weatherStation = WeatherStationData(authorization)         # Test DEVICELIST
    except NoDevice:
        if stdout.isatty():
            print("lnetatmo.py : warning, no weather station available for testing")
    else:
        weatherStation.MinMaxTH()                          # Test GETMEASUR


    try:
        homes = HomeData(authorization)
    except NoDevice :
        if stdout.isatty():
            print("lnetatmo.py : warning, no home available for testing")

    try:
        thermostat = ThermostatData(authorization)
    except NoDevice:
        if stdout.isatty():
            print("lnetatmo.py : warning, no thermostat avaible for testing")

    # If we reach this line, all is OK

    # If launched interactively, display OK message
    if stdout.isatty():
        print("lnetatmo.py : OK")

    exit(0)
