netatmo-api-python
==================

Simple API to access Netatmo weather station data from any python script
For more detailed information see http://dev.netatmo.com

I have no relation with the netatmo company, I wrote this because I needed it myself,
and published it to save time to anyone who would have same needs.

I am trying to make this library survive to continuous Netatmo changes but their habbit to introduce breaking changes anytime without notice make this target hard to reach.

>BREAKING CHANGEi (july 2023): Netatmo seems no longer (july 2023) to allow grant_type "password", even for an app credentials that belong to the same account than the home. They have added the capability of creating access_token/refresh_token couple from the dev page (the location where app are created). As a consequence, the username/password credentials can no longer be used and you must replace them with a new parameter REFRESH_TOKEN that you will get from the web interface. To get this token, you are required to specify the scope you want to allow to this token. Select all that apply for your library use.

>NEW BREAKING CHANGE (december 2023): Web generated refresh_tokens are no more long lived tokens, they will be automatically refreshed. Consequences : No more static authentication in the library source and ~/.netatmo-credentials file will be updated to reflect change in the refresh token. This file MUST be writable and if you run Netatmo tools in container, remember to persist this file between container run.

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
