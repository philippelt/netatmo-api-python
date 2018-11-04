"""
coding=utf-8
"""
import warnings, time

from . import NoDevice, postRequest, todayStamps, _BASE_URL

_GETMEASURE_REQ = _BASE_URL + "api/getmeasure"
_GETSTATIONDATA_REQ = _BASE_URL + "api/getstationsdata"

class WeatherStationData:
    """
    List the Weather Station devices (stations and modules)
    Args:
        authData (ClientAuth): Authentication information with a working access Token
    """
    def __init__(self, authData, urlReq=None):
        self.urlReq = urlReq or _GETMEASURE_REQ
        self.getAuthToken = authData.accessToken
        postParams = {
                "access_token": self.getAuthToken
                }
        resp = postRequest(self.urlReq, postParams)
        self.rawData = resp['body']['devices']
        if not self.rawData : raise NoDevice("No weather station available")
        self.stations = { d['_id'] : d for d in self.rawData }
        self.modules = dict()
        for i in range(len(self.rawData)):
            if 'modules' not in self.rawData[i]:
                self.rawData[i]['modules'] = [ self.rawData[i] ]
            for m in self.rawData[i]['modules']:
                if 'module_name' not in m:
                    continue
                self.modules[ m['_id'] ] = m
                self.modules[ m['_id'] ][ 'main_device' ] = self.rawData[i]['_id']
        self.default_station = list(self.stations.values())[0]['station_name']

    def modulesNamesList(self, station=None):
        res = set([m['module_name'] for m in self.modules.values()])
        if station:
            res.add(self.stationByName(station)['module_name'])
        else:
            for id,station in self.stations.items():
                res.add(station['module_name'])
        return list(res)

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
            elif s['module_name'] == module:
                return s
        else:
            for id, station in self.stations.items():
                if station['module_name'] == module:
                    return station
        for m in self.modules:
            mod = self.modules[m]
            if mod['module_name'] == module :
                if not s or mod['main_device'] == s['_id'] : return mod
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

    def monitoredConditions(self, module):
        mod = self.moduleByName(module)
        conditions = []
        for cond in mod['data_type']:
            if cond == 'Wind':
                # the Wind meter actually exposes the following conditions
                conditions.extend(['windangle', 'windstrength', 'gustangle', 'guststrength'])
            else:
                conditions.append(cond.lower())
        if mod['type'] == 'NAMain':
            # the main module has wifi_status
            conditions.append('wifi_status')
        else:
            # assume all other modules have rf_status, battery_vp, and battery_percent
            conditions.extend(['rf_status', 'battery_vp', 'battery_percent'])
        return conditions

    def lastData(self, station=None, exclude=0):
        s = self.stationByName(station)
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
            if 'dashboard_data' not in module:
                continue
            ds = module['dashboard_data']
            if ds['time_utc'] > limit :
                lastD[module['module_name']] = ds.copy()
                lastD[module['module_name']]['When'] = lastD[module['module_name']].pop("time_utc")
                # For potential use, add battery and radio coverage information to module data if present
                for i in ('rf_status', 'battery_vp', 'battery_percent') :
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
