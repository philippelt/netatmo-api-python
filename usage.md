Python Netatmo API programmers guide
------------------------------------



>2013-01-21, philippelt@users.sourceforge.net
>2014-01-13, Revision to include new modules additionnal informations


No additional libraries other than standard Python library is required.

Both Python2 and Python3 are supported without change.

More information about the Netatmo REST API can be obtained from http://dev.netatmo.com/doc/

This package support only user based authentication (i.e. must provide user credentials to access data).



### 1 Setup your environment from Netatmo ###




Before being able to use the module you will need :

  * A Netatmo web user account having access to, at least, one station
  * An application registered from the user account (see http://dev.netatmo.com/dev/createapp) to obtain application credentials.

In the netatmo philosophy, both the application accessing and the user account used to gain access to a station have to be registered thus have authentication credentials.



### 2 Setup your library ###



Copy the lnetatmo.py file in your work directory (or your platform choice of user libraries).

To ease future uses, I suggest that you hardcode in the library your application and user credentials. This is not mandatory as this parameters can be explicitly passed at authentication phase.

If you want to do it, just edit the source file and hard code required values for :


```python
_CLIENT_ID     = "<your client_id>"
_CLIENT_SECRET = "<your client_secret>"
_USERNAME      = "<netatmo username>"
_PASSWORD      = "<netatmo user password>"
```


If you provide all the values, you can test that everything is working properly by simply running the package as a standalone program.

This will run a full access test to the account and stations and return 0 as return code if everything works well. If run interactively, it will also display an OK message.

```bash
$ python3 lnetatmo.py
lnetatmo.py : OK
$ echo $?
0
```



### 3 Package guide ###

  

Most of the time, the sequence of operations will be :

  1. Authenticate your program against Netatmo web server
  2. Get the device list accessible to the user
  3. Ask for data on one of these devices


Example :

```python
#!/usr/bin/python3
# encoding=utf-8

import lnetatmo

authorization = lnetatmo.ClientAuth()
devList = lnetatmo.DeviceList(authorization)
print ("Current temperature (inside/outside): %s / %s °C" %
            ( devList.lastData()['<my internal sensor name>']['Temperature'],
              devList.lastData()['<my external sensor name>']['Temperature'])
)
```

In this example, no init parameters are supplied to ClientAuth, the library is supposed to have been customized with the required values (see §2).

The Netatmo design is based on stations (usually the in-house module) and modules (radio sensors reporting to a station, usually an outdoor sensor).

Sensor designed is not exactly the same and are not addresses the same way. This may probably evolved in the future with some clarification on the station role (the reporting device) and module role (getting environmental data). The fact that a sensor is physically built in the station should not interfere.

The consequence is that, for the API, we will use terms of station data (for the sensors inside the station) and module data (for external(s) module). Lookup methods like moduleByName look for external modules and NOT station
modules.


>Exception : to reflect again the API structure, the last data uploaded by the station are indexed by module name (internal and external).


Sensors (stations and modules) are managed in the API using ID's (mac address for the station and an equivalent Zigbee mac or else for modules). The Netatmo web account management gives you the capability to associate names to station sensor and module (and to the station itself). This is by far more comfortable and the interface provides service to locate a station or a module by name or by Id depending of your taste. Module lookup by name includes the optional station name in case
multiple stations would have similar module names.

The results are Python data structures, mostly dictionaries as they mirror easily the JSON returned data. All supplied classes provides simple properties to use as well as access to full data returned by the netatmo web services (rawData property for most classes).



### 4 Package classes and functions ###



#### 4-1 Global variables ####

  
```python
_CLIENT_ID, _CLIENT_SECRET = Application ID and secret provided by Netatmo
application registration in your user account

_USERNAME, _PASSWORD : Username and password of your netatmo account

_BASE_URL and _*_REQ : Various URL to access Netatmo web services. They are
documented in http://dev.netatmo.com/doc/ They should not be changed unless
Netatmo API changes.
```  



#### 4-2 ClientAuth class ####



Constructor

```python
    authorization = lnetatmo.ClientAuth( clientId = _CLIENT_ID,
                                         clientSecret = _CLIENT_SECRET,
                                         username = _USERNAME,
                                         password = _PASSWORD
                                        )
```


Requires : Application and User credentials to access Netatmo API. if all this parameters are put in global variables they are not required (in library source code or in the main program through lnetatmo._CLIENT_ID = …)


Return : an authorization object that will supply the access token required by other web services. This class will handle the renewal of the access token if expiration is reached.


Properties, all properties are read-only unless specified :

  * **accessToken** : Retrieve a valid access token (renewed if necessary)
  * **refreshToken** : The token used to renew the access token (normally should not be used)
  * **expiration** : The expiration time (epoch) of the current token

  

#### 4-3 User class ####



Constructor

```python
    user = lnetatmo.User( authorization )
```


Requires : an authorization object (ClientAuth instance)


Return : a User object. This object provides multiple informations on the user account such as the mail address of the user, the preferred language, …


Properties, all properties are read-only unless specified :


  * **rawData** : Full dictionary of the returned JSON GETUSER Netatmo API service
  * **id** : user Netatmo unique ID
  * **ownerMail** : eMail address associated to the user account
  * **devList** : List of Station's id accessible to the user account


In most cases, you will not need to use this class that is oriented toward an application that would use the other authentication method to an unknown user and then get information about him.



#### 4-4 DeviceList class ####



Constructor

```python
    devList = lnetatmo.DeviceList( authorization )
```


Requires : an authorization object (ClientAuth instance)


Return : a DeviceList object. This object contains most administration properties of stations and modules accessible to the user and the last data pushed by the station to the Netatmo servers.


Properties, all properties are read-only unless specified:


  * **rawData** : Full dictionary of the returned JSON DEVICELIST Netatmo API service
  * **default_station** : Name of the first station returned by the web service (warning, this is mainly for the ease of use of peoples having only 1 station).
  * **stations** : Dictionary of stations (indexed by ID) accessible to this user account
  * **modules** : Dictionary of modules (indexed by ID) accessible to the user account (whatever station there are plugged in)


Methods :


  * **stationByName** (station=None) : Find a station by it's station name
    * Input : Station name to lookup (str)
    * Output : station dictionary or None
  * **stationById** (sid) : Find a station by it's Netatmo ID (mac address)
    * Input : Station ID
    * Output : station dictionary or None
  * **moduleByName** (module, station=None) : Find a module by it's module name
    * Input : module name and optional station name
    * Output : module dictionary or None

     The station name parameter, if provided, is used to check wether the module belongs to the appropriate station (in case multiple stations would have same module name).

  * **moduleById** (mid, sid=None) : Find a module by it's ID and belonging station's ID
    * Input : module ID and optional Station ID
    * Output : module dictionary or None
  * **lastData** (station=None, exclude=0) : Get the last data uploaded by the station, exclude sensors with measurement older than given value (default return all)
    * Input : station name OR id. If not provided default_station is used. Exclude is the delay in seconds from now to filter sensor readings.
    * Output : Sensors data dictionary (Key is sensor name)

     AT the time of this document, Available measures types are :
      * a full or subset of Temperature, Pressure, Noise, Co2, Humidity, When (measurement timestamp) for modules including station module
      * battery_vp : likely to be total battery voltage for external sensors (running on batteries) in mV (undocumented)
      * rf_status : likely to be the % of radio signal between the station and a module (undocumented)

     See Netatmo API documentation for units of regular measurements

     If you named the internal sensor 'indoor' and the outdoor one 'outdoor' (simple is'n it ?) for your station in the user Web account station properties, you will access the data by :

```python
# Last data access example

theData = devList.lastData()
theData['indoor']['Co2']          # To get the last CO2 measure of station
theData['outdoor']['Temperature']  # To get outside temperature
```
  * **checkNotUpdated** (station=None, delay=3600) :
    * Input : optional station name (else default_station is used)
    * Output : list of modules name for which last data update is older than specified delay (default 1 hour). If the station itself is lost, the module_name of the station will be returned (the key item of lastData information).

     For example (following the previous one)

```python
# Ensure data sanity

for m in devList.checkNotUpdated("<optional station name>"):
    print("Warning, sensor %s information is obsolete" % m)
    if moduleByName(m) == None : # Sensor is not an external module
        print("The station is lost")
```
  * **checkUpdated** (station=None, delay=3600) :
    * Input : optional station name (else default_station is used)
    * Output : list of modules name for which last data update is newer than specified delay (default 1 hour).

     Complement of the previous service

  * **getMeasure** (device_id, scale, mtype, module_id=None, date_begin=None, date_end=None, limit=None, optimize=False) :
    * Input : All parameters specified in the Netatmo API service GETMEASURE (type being a python reserved word as been replaced by mtype).
    * Output : A python dictionary reflecting the full service response. No transformation is applied.
  * **MinMaxTH** (station=None, module=None, frame="last24") : Return min and max temperature and humidity for the given station/module in the given timeframe
    * Input :
      * An optional station Name or ID, default_station is used if not supplied,
      * An optional module name or ID, default : station sensor data is used
      * A time frame that can be :
        * "last24" : For a shifting window of the last 24 hours
        * "day" : For all available data in the current day
    * Output :
      * A 4 values tuple (Temp mini, Temp maxi, Humid mini, Humid maxi)

     >Note : I have been oblliged to determine the min and max manually, the built-in service in the API doesn't always provide the actual min and max. The double parameter (scale) and aggregation request (min, max) is not satisfying
at all if you slip over two days as required in a shifting 24 hours window.


#### 4-5 Utilities functions ####


  * **toTimeString** (timestamp) : Convert a Netatmo time stamp to a readable date/time format.
  * **toEpoch**( dateString) : Convert a date string (form YYYY-MM-DD_HH:MM:SS) to timestamp
  * **todayStamps**() : Return a couple of epoch time (start, end) for the current day


#### 4-6 All-in-One function ####


If you just need the current temperature and humidity reported by a sensor with associated min and max values on the last 24 hours, you can get it all with only one call that handle all required steps including authentication :


**getStationMinMaxTH**(station=None, module=None) :
  * Input : optional station name and/or module name (if no station name is provided, default_station will be used, if no module name is provided, station sensor will be reported).
  * Output : A tuple of 6 values (Temperature, Humidity, minT, MaxT, minH, maxH)

```python
>>> import lnetatmo
>>> print(lnetatmo.getStationMinMaxTH())
[20, 33, 18.1, 20, 30, 34]
>>>
>>> print(lnetatmo.getStationMinMaxTH("My Station name", "external module"))
[2, 53, 1.2, 5.4, 51, 74]
