netatmo-api-python
==================

Simple API to access Netatmo weather station data from any python script
For more detailed information see http://dev.netatmo.com

I have no relation with the netatmo company, I wrote this because I needed it myself,
and published it to save time to anyone who would have same needs.

Following the implementation of "Home" everywhere in the Netatmo API with various behavior, the library has been adjusted to include the home parameters in most calls.
If you are using a single account with a single home and single weather station, the library has been implemented so that your code should continue to run without change.

If you have multiple homes or were supplying a station name in some method calls, you will have to adapt your code :
 - to supply a home name when looking for data for most class initializers
 - to use the new station name set by Netatmo (which is not your previously set value)
  
>BREAKING CHANGE: Netatmo seems no longer (july 2023) to allow grant_type "password", even for an app credentials that belong to the same account than the home. They have added the capability of creating access_token/refresh_token couple from the dev page (the location where app are created). As a consequence, the username/password credentials can no longer be used and you must replace them with a new parameter REFRESH_TOKEN that you will get from the web interface. To get this token, you are required to specify the scope you want to allow to this token. Select all that apply for your library use.

>SHORT VERSION TO UPGRADE: If you where using a netatmo_credentials file, juste remove USERNAME and PASSWORD fields and add a REFRESH_TOKEN field which value is the one you will obtain from the https://dev.netatmo.com in MyApps selecting you app and using "Token Generator" after selecting required scopes.

### Install ###

To install lnetatmo simply run:

    python setup.py install

  or

    pip install lnetatmo

Depending on your permissions you might be required to use sudo.

It is a single file module, on platforms where you have limited access, you just have to clone the repo and take the lnetatmo.py in the same directory than your main program.

Once installed you can simple add lnetatmo to your python scripts by including:

    import lnetatmo

For documentation, see usage
