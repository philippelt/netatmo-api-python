# Locate the camera name "MyCam" IP on the local LAN
# to collect a snapshot of what the camera sees without
# bandwith constraints of the Internet connexion


# You will need the "requests" library :  pip install requests

from sys import exit
import lnetatmo
import requests


# The name I gave the camera in the Netatmo Security App
MY_CAMERA = "MyCam"
# From the netatmo camera API documentation
SNAPSHOT_REQUEST = "/live/snapshot_720.jpg"


# Authenticate (see authentication in documentation)
# Note you will need the appropriate scope (read_welcome access_welcome or read_presence access_presence)
# depending of the camera you are trying to reach
# The default library scope ask for all aceess to all cameras
authorization = lnetatmo.ClientAuth()

# Gather Home information (available cameras and other infos)
homeData = lnetatmo.HomeData(authorization)

# Ask for Url giving local access to the camera I am looking for
# Or remote VPN access through Netatmo server if the camera can't be reach locally
vpnUrl, localUrl = homeData.cameraUrls(MY_CAMERA)
camUrl = localUrl if localUrl else vpnUrl

# Request a snapshot from the camera
r = requests.get(camUrl + SNAPSHOT_REQUEST)

# If all was Ok, I should have a returned HTTP status of 200, else something goes wrong
if r.status_code != 200 :
    # Decide what to do with an error situation (alert, log, ...)
    exit(1)

# Save the snapshot in a file
with open("MyCamSnap.jpg", "wb") as f: f.write(r.content)

# You can then archive the file, send it by mail, message App, ...

exit(0)
