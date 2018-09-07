"""
coding=utf-8
"""
import time

from . import postRequest, _BASE_URL

_GETPUBLIC_DATA = _BASE_URL + "api/getpublicdata"
_LON_NE = 6.221652
_LAT_NE = 46.610870
_LON_SW = 6.217828
_LAT_SW = 46.596485

_STATION_TEMPERATURE_TYPE = "temperature"
_STATION_PRESSURE_TYPE = "pressure"
_STATION_HUMIDITY_TYPE = "humidity"

_ACCESSORY_RAIN_LIVE_TYPE = "rain_live"
_ACCESSORY_RAIN_60MIN_TYPE = "rain_60min"
_ACCESSORY_RAIN_24H_TYPE = "rain_24h"
_ACCESSORY_RAIN_TIME_TYPE = "rain_timeutc"
_ACCESSORY_WIND_STRENGTH_TYPE = "wind_strength"
_ACCESSORY_WIND_ANGLE_TYPE = "wind_angle"
_ACCESSORY_WIND_TIME_TYPE = "wind_timeutc"
_ACCESSORY_GUST_STRENGTH_TYPE = "gust_strength"
_ACCESSORY_GUST_ANGLE_TYPE = "gust_angle"


class PublicData:

    def __init__(self,
                 auth_data,
                 LAT_NE=_LAT_NE,
                 LON_NE=_LON_NE,
                 LAT_SW=_LAT_SW,
                 LON_SW=_LON_SW,
                 required_data_type=None,  # comma-separated list from above _STATION or _ACCESSORY values
                 filtering=False):
        self.getAuthToken = auth_data.accessToken
        post_params = {
            "access_token": self.getAuthToken,
            "lat_ne": LAT_NE,
            "lon_ne": LON_NE,
            "lat_sw": LAT_SW,
            "lon_sw": LON_SW,
            "filter": filtering
            }

        if required_data_type:
            post_params['required_data'] = required_data_type

        resp = postRequest(_GETPUBLIC_DATA, post_params)
        self.raw_data = resp['body']
        self.status = resp['status']
        self.time_exec = toTimeString(resp['time_exec'])
        self.time_server = toTimeString(resp['time_server'])

    def CountStationInArea(self):
        return len(self.raw_data)

    # Backwards compatibility for < 1.2
    def getLive(self):
        return self.getLatestRain()

    def getLatestRain(self):
        return self.getAccessoryMeasures(_ACCESSORY_RAIN_LIVE_TYPE)

    def getAverageRain(self):
        return averageMeasure(self.getLatestRain())

    # Backwards compatibility for < 1.2
    def get60min(self):
        return self.get60minRain()

    def get60minRain(self):
        return self.getAccessoryMeasures(_ACCESSORY_RAIN_60MIN_TYPE)

    def getAverage60minRain(self):
        return averageMeasure(self.get60minRain())

    # Backwards compatibility for < 1.2
    def get24h(self):
        return self.get24hRain()

    def get24hRain(self):
        return self.getAccessoryMeasures(_ACCESSORY_RAIN_24H_TYPE)

    def getAverage24hRain(self):
        return averageMeasure(self.get24hRain())

    def getLatestPressures(self):
        return self.getLatestStationMeasures(_STATION_PRESSURE_TYPE)

    def getAveragePressure(self):
        return averageMeasure(self.getLatestPressures())

    def getLatestTemperatures(self):
        return self.getLatestStationMeasures(_STATION_TEMPERATURE_TYPE)

    def getAverageTemperature(self):
        return averageMeasure(self.getLatestTemperatures())

    def getLatestHumidities(self):
        return self.getLatestStationMeasures(_STATION_HUMIDITY_TYPE)

    def getAverageHumidity(self):
        return averageMeasure(self.getLatestHumidities())

    def getLatestWindStrengths(self):
        return self.getAccessoryMeasures(_ACCESSORY_WIND_STRENGTH_TYPE)

    def getAverageWindStrength(self):
        return averageMeasure(self.getLatestWindStrengths())

    def getLatestWindAngles(self):
        return self.getAccessoryMeasures(_ACCESSORY_WIND_ANGLE_TYPE)

    def getLatestGustStrengths(self):
        return self.getAccessoryMeasures(_ACCESSORY_GUST_STRENGTH_TYPE)

    def getAverageGustStrength(self):
        return averageMeasure(self.getLatestGustStrengths())

    def getLatestGustAngles(self):
        return self.getAccessoryMeasures(_ACCESSORY_GUST_ANGLE_TYPE)

    def getLocations(self):
        locations = {}
        for station in self.raw_data:
            locations[station['_id']] = station['place']['location']
        return locations

    # Backwards compatibility for < 1.2
    def getTimeforMeasure(self):
        return self.getTimeForRainMeasures()

    def getTimeForRainMeasures(self):
        return self.getAccessoryMeasures(_ACCESSORY_RAIN_TIME_TYPE)

    def getTimeForWindMeasures(self):
        return self.getAccessoryMeasures(_ACCESSORY_WIND_TIME_TYPE)

    def getLatestStationMeasures(self, type):
        measures = {}
        for station in self.raw_data:
            for _, module in station['measures'].items():
                if 'type' in module and type in module['type'] and 'res' in module and module['res']:
                    measure_index = module['type'].index(type)
                    latest_timestamp = sorted(module['res'], reverse=True)[0]
                    measures[station['_id']] = module['res'][latest_timestamp][measure_index]
        return measures

    def getAccessoryMeasures(self, type):
        measures = {}
        for station in self.raw_data:
            for _, module in station['measures'].items():
                if type in module:
                    measures[station['_id']] = module[type]
        return measures


def toTimeString(value):
    return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(int(value)))


def averageMeasure(measures):
    if measures:
        return sum(measures.values()) / len(measures)
    else:
        return 0.0
