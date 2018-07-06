"""
coding=utf-8
"""
import warnings, time

from . import NoDevice, postRequest, todayStamps, _BASE_URL                                                                                                                 

_GETPUBLIC_DATA = _BASE_URL + "api/getpublicdata"
_LON_NE = 6.221652
_LAT_NE = 46.610870
_LON_SW = 6.217828
_LAT_SW = 46.596485

class PublicData:

    def __init__(self,
                authData,
                LAT_NE = _LAT_NE,
                LON_NE = _LON_NE,
                LAT_SW = _LAT_SW,
                LON_SW=_LON_SW,
                required_data_type = "rain", # "humidity" is the only 2nd choice
                filtering=False):                                                                                                                                                   
        self.getAuthToken = authData.accessToken
        postParams = {
            "access_token" : self.getAuthToken,
            "lat_ne" : LAT_NE,
            "lon_ne" : LON_NE,
            "lat_sw" : LAT_SW,
            "lon_sw" : LON_SW,
            "required_data" : required_data_type,
            "filter" : filtering
            }
        resp = postRequest(_GETPUBLIC_DATA, postParams)
        self.rawData = resp['body']
        self.status = resp['status']
        self.time_exec = toTimeString(resp['time_exec'])
        self.time_server = toTimeString(resp['time_server'])


    def CountStationInArea(self):
        return len(self.rawData)

    def get24h(self):
        measures = {} # dict
        for station in self.rawData:
            for module in station['measures']:
                for typeModule in station['measures'][module]:
                    if typeModule == 'rain_24h':
                        measures[station['_id']] = station['measures'][module]['rain_24h']
        return measures


    def get60min(self):
        measures = {} # dict
        for station in self.rawData:
            for module in station['measures']:
                for typeModule in station['measures'][module]:
                    if typeModule == 'rain_60min':
                        measures[station['_id']] = station['measures'][module]['rain_60min']
        return measures

    def getLive(self):
        measures = {} # dict
        for station in self.rawData:
            for module in station['measures']:
                for typeModule in station['measures'][module]:
                    if typeModule == 'rain_live':
                        measures[station['_id']] = station['measures'][module]['rain_live']
        return measures

    def getLocations(self):
        locations = {} #dict
        for station in self.rawData:
            locations [station['_id']] = station['place']['location']
        return locations

    def getTimeforMeasure(self):
        measures_timestamps = {} # dict
        for station in self.rawData:
            for module in station['measures']:
                for typeModule in station['measures'][module]:
                    if typeModule == 'rain_timeutc':            
                        measures_timestamps[station['_id']] = station['measures'][module]['rain_timeutc']
        return measures_timestamps



def toTimeString(value):
    return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(int(value)))
