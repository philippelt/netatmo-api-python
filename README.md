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
