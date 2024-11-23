netatmo-api-python
==================

Simple API to access Netatmo weather station data from any python script
For more detailed information see http://dev.netatmo.com

I have no relation with the netatmo company, I wrote this because I needed it myself,
and published it to save time to anyone who would have same needs.

There is no longer credential load at library import, credentials are loaded at `ClientAuth` class initialization and a new parameter `credentialFile` allow to specify private name and location for the credential file. It is recommended to use this parameter to specify the location of the credential file using absolute path to be able to be independant of the account used to run the program.
>[!CAUTION]
> Remember that the program using the library **must** be able to rewrite the credential file to be able to save the new refresh token that netatmo may provide at the authentication step. Check the file permission according to the account the program is running.

>[!NOTE]
> Several users reported that Netatmo is now asking for a DPO (Data Protection Officer) mail address to deliver application credentials. Netatmo is requesting this to comply with RGPD European regulation for the case of your application would be able to access other customers account and you would hold responsibility to protect others potentially confidential informations.  
> For most users (if not all) of this library, this is totally useless as we are accessing only OUR devices thus are not concerned by RGPD. You can then put your netatmo account email address, just in case some mail would be sent to it.  
> It is only an information for the Netatmo records, there is absolutely no use of this information by the library.

>[!CAUTION]
> There are currently frequent authentication failures with Netatmo servers, returning exception ranging from 500 errors to invalid scope. Please check that you are not facing a transient failure by retrying your code some minutes later before reporting an issue.

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
