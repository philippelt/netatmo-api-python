"""
coding=utf-8
"""
from .WeatherStation import WeatherStationData

from . import _BASE_URL

_GETHOMECOACHDATA_REQ = _BASE_URL + "api/gethomecoachsdata"


class HomeCoachData(WeatherStationData):
    """
    List the Home Couch devices (stations and modules)
    Args:
        authData (ClientAuth): Authentication information with a working access Token
    """
    def __init__(self, authData):
       super(HomeCoachData, self).__init__(authData, urlReq=_GETHOMECOACHDATA_REQ)
