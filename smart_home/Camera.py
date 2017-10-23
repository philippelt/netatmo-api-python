"""
coding=utf-8
"""
import imghdr
import time

from urllib.error import URLError
from . import NoDevice, postRequest, _BASE_URL

_GETHOMEDATA_REQ = _BASE_URL + "api/gethomedata"
_GETCAMERAPICTURE_REQ = _BASE_URL + "api/getcamerapicture"
_GETEVENTSUNTIL_REQ = _BASE_URL + "api/geteventsuntil"


class CameraData:
    """
    List the Netatmo cameras informations
        (Homes, cameras, modules, events, persons)
    Args:
        authData (ClientAuth):
            Authentication information with a working access Token
    """
    def __init__(self, authData, size=15):
        self.getAuthToken = authData.accessToken
        postParams = {
            "access_token": self.getAuthToken,
            "size": size
            }
        resp = postRequest(_GETHOMEDATA_REQ, postParams)
        self.rawData = resp['body']
        self.homes = {d['id']: d for d in self.rawData['homes']}
        if not self.homes:
            raise NoDevice("No camera available")
        self.persons = dict()
        self.events = dict()
        self.outdoor_events = dict()
        self.cameras = dict()
        self.modules = dict()
        self.lastEvent = dict()
        self.outdoor_lastEvent = dict()
        self.types = dict()
        for i in range(len(self.rawData['homes'])):
            nameHome = self.rawData['homes'][i]['name']
            if nameHome not in self.cameras:
                self.cameras[nameHome] = dict()
            if nameHome not in self.types:
                self.types[nameHome] = dict()
            for p in self.rawData['homes'][i]['persons']:
                self.persons[p['id']] = p
            for e in self.rawData['homes'][i]['events']:
                if e['type'] == 'outdoor':
                    if e['camera_id'] not in self.outdoor_events:
                        self.outdoor_events[e['camera_id']] = dict()
                    self.outdoor_events[e['camera_id']][e['time']] = e
                elif e['type'] != 'outdoor':
                    if e['camera_id'] not in self.events:
                        self.events[e['camera_id']] = dict()
                    self.events[e['camera_id']][e['time']] = e
            for c in self.rawData['homes'][i]['cameras']:
                self.cameras[nameHome][c['id']] = c
                if c['type'] == 'NACamera' and 'modules' in c :
                    for m in c['modules']:
                        self.modules[m['id']] = m
                        self.modules[m['id']]['cam_id'] = c['id']
            for t in self.rawData['homes'][i]['cameras']:
                self.types[nameHome][t['type']] = t
        for camera in self.events:
            self.lastEvent[camera] = self.events[camera][
                sorted(self.events[camera])[-1]]
        for camera in self.outdoor_events:
            self.outdoor_lastEvent[camera] = self.outdoor_events[camera][
                sorted(self.outdoor_events[camera])[-1]]
        self.default_home = list(self.homes.values())[0]['name']
        if self.modules != {}:
            self.default_module = list(self.modules.values())[0]['name']
        else:
            self.default_module = None
        self.default_camera = list(self.cameras[self.default_home].values())[0]

    def homeById(self, hid):
        return None if hid not in self.homes else self.homes[hid]

    def homeByName(self, home=None):
        if not home:
            return self.homeByName(self.default_home)
        for key, value in self.homes.items():
            if value['name'] == home:
                return self.homes[key]

    def cameraById(self, cid):
        for home, cam in self.cameras.items():
            if cid in self.cameras[home]:
                return self.cameras[home][cid]
        return None

    def cameraByName(self, camera=None, home=None):
        if not camera and not home:
            return self.default_camera
        elif home and camera:
            if home not in self.cameras:
                return None
            for cam_id in self.cameras[home]:
                if self.cameras[home][cam_id]['name'] == camera:
                    return self.cameras[home][cam_id]
        elif not home and camera:
            for home, cam_ids in self.cameras.items():
                for cam_id in cam_ids:
                    if self.cameras[home][cam_id]['name'] == camera:
                        return self.cameras[home][cam_id]
        else:
            return list(self.cameras[home].values())[0]
        return None

    def moduleById(self, mid):
        return None if mid not in self.modules else self.modules[mid]

    def moduleByName(self, module=None, camera=None, home=None):
        if not module:
            if self.default_module:
                return self.moduleByName(self.default_module)
            else:
                return None
        cam = None
        if camera or home:
            cam = self.cameraByName(camera, home)
            if not cam:
                return None
        for key, value in self.modules.items():
            if value['name'] == module:
                if cam and value['cam_id'] != cam['id']:
                    return None
                return self.modules[key]
        return None

    def cameraType(self, camera=None, home=None, cid=None):
        """
        Return the type of a given camera.
        """
        cameratype = None
        if cid:
            camera_data = self.cameraById(cid)
        else:
            camera_data = self.cameraByName(camera=camera, home=home)
        if camera_data:
            cameratype = camera_data['type']
        return cameratype

    def cameraUrls(self, camera=None, home=None, cid=None):
        """
        Return the vpn_url and the local_url (if available) of a given camera
        in order to access to its live feed
        """
        local_url = None
        vpn_url = None
        if cid:
            camera_data = self.cameraById(cid)
        else:
            camera_data = self.cameraByName(camera=camera, home=home)
        if camera_data:
            vpn_url = camera_data['vpn_url']
            if camera_data['is_local']:
                try:
                    resp = postRequest('{0}/command/ping'.format(
                        camera_data['vpn_url']), dict())
                    temp_local_url = resp['local_url']
                except URLError:
                    return None, None

                try:
                    resp = postRequest('{0}/command/ping'.format(
                        temp_local_url), dict())
                    if temp_local_url == resp['local_url']:
                        local_url = temp_local_url
                except URLError:
                    pass
        return vpn_url, local_url

    def personsAtHome(self, home=None):
        """
        Return the list of known persons who are currently at home
        """
        if not home:
            home = self.default_home
        home_data = self.homeByName(home)
        atHome = []
        for p in home_data['persons']:
            # Only check known persons
            if 'pseudo' in p:
                if not p["out_of_sight"]:
                    atHome.append(p['pseudo'])
        return atHome

    def getCameraPicture(self, image_id, key):
        """
        Download a specific image (of an event or user face) from the camera
        """
        postParams = {
            "access_token": self.getAuthToken,
            "image_id": image_id,
            "key": key
            }
        resp = postRequest(_GETCAMERAPICTURE_REQ, postParams)
        image_type = imghdr.what('NONE.FILE', resp)
        return resp, image_type

    def getProfileImage(self, name):
        """
        Retrieve the face of a given person
        """
        for p in self.persons:
            if 'pseudo' in self.persons[p]:
                if name == self.persons[p]['pseudo']:
                    image_id = self.persons[p]['face']['id']
                    key = self.persons[p]['face']['key']
                    return self.getCameraPicture(image_id, key)
        return None, None

    def updateEvent(self, event=None, home=None, cameratype=None):
        """
        Update the list of event with the latest ones
        """
        if not home:
            home = self.default_home
        if cameratype == 'NACamera':
            # for the Welcome camera
            if not event:
                # If not event is provided we need to retrieve the oldest of
                # the last event seen by each camera
                listEvent = dict()
                for cam_id in self.lastEvent:
                    listEvent[self.lastEvent[cam_id]['time']] =\
                        self.lastEvent[cam_id]
                event = listEvent[sorted(listEvent)[0]]
        if cameratype == 'NOC':
            # for the Presence camera
            if not event:
                # If not event is provided we need to retrieve the oldest of
                # the last event seen by each camera
                listEvent = dict()
                for cam_id in self.outdoor_lastEvent:
                    listEvent[self.outdoor_lastEvent[cam_id]['time']] =\
                        self.outdoor_lastEvent[cam_id]
                event = listEvent[sorted(listEvent)[0]]

        home_data = self.homeByName(home)
        postParams = {
                "access_token": self.getAuthToken,
                "home_id": home_data['id'],
                "event_id": event['id']
            }
        resp = postRequest(_GETEVENTSUNTIL_REQ, postParams)
        eventList = resp['body']['events_list']
        for e in eventList:
            if e['type'] == 'outdoor':
                self.outdoor_events[e['camera_id']][e['time']] = e
            elif e['type'] != 'outdoor':
                self.events[e['camera_id']][e['time']] = e
        for camera in self.events:
                self.lastEvent[camera] = self.events[camera][
                        sorted(self.events[camera])[-1]]
        for camera in self.outdoor_events:
                self.outdoor_lastEvent[camera] = self.outdoor_events[camera][
                        sorted(self.outdoor_events[camera])[-1]]

    def personSeenByCamera(self, name, home=None, camera=None, exclude=0):
        """
        Return True if a specific person has been seen by a camera
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            print("personSeenByCamera: Camera name or home is unknown")
            return False
        # Check in the last event is someone known has been seen
        if exclude:
            limit = (time.time() - exclude)
            array_time_event = sorted(self.events[cam_id])
            array_time_event.reverse()
            for time_ev in array_time_event:
                if time_ev < limit:
                    return False
                elif self.events[cam_id][time_ev]['type'] == 'person':
                    person_id = self.events[cam_id][time_ev]['person_id']
                    if 'pseudo' in self.persons[person_id]:
                        if self.persons[person_id]['pseudo'] == name:
                            return True
        elif self.lastEvent[cam_id]['type'] == 'person':
            person_id = self.lastEvent[cam_id]['person_id']
            if 'pseudo' in self.persons[person_id]:
                if self.persons[person_id]['pseudo'] == name:
                    return True
        return False

    def _knownPersons(self):
        known_persons = dict()
        for p_id, p in self.persons.items():
            if 'pseudo' in p:
                known_persons[p_id] = p
        return known_persons

    def knownPersonsNames(self):
        names = []
        for p_id,p in self._knownPersons().items():
            names.append(p['pseudo'])
        return names

    def someoneKnownSeen(self, home=None, camera=None, exclude=0):
        """
        Return True if someone known has been seen
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            print("someoneKnownSeen: Camera name or home is unknown")
            return False

        if exclude:
            limit = (time.time() - exclude)
            array_time_event = sorted(self.events[cam_id])
            array_time_event.reverse()
            for time_ev in array_time_event:
                if time_ev < limit:
                    return False
                elif self.events[cam_id][time_ev]['type'] == 'person':
                    if self.events[cam_id][time_ev][
                            'person_id'] in self._knownPersons():
                        return True
        # Check in the last event is someone known has been seen
        elif self.lastEvent[cam_id]['type'] == 'person':
            if self.lastEvent[cam_id]['person_id'] in self._knownPersons():
                return True
        return False

    def someoneUnknownSeen(self, home=None, camera=None, exclude=0):
        """
        Return True if someone unknown has been seen
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            print("someoneUnknownSeen: Camera name or home is unknown")
            return False

        if exclude:
            limit = (time.time() - exclude)
            array_time_event = sorted(self.events[cam_id])
            array_time_event.reverse()
            for time_ev in array_time_event:
                if time_ev < limit:
                    return False
                elif self.events[cam_id][time_ev]['type'] == 'person':
                    if self.events[cam_id][time_ev][
                            'person_id'] not in self._knownPersons():
                        return True
        # Check in the last event is someone known has been seen
        elif self.lastEvent[cam_id]['type'] == 'person':
            if self.lastEvent[cam_id]['person_id'] not in self._knownPersons():
                return True
        return False

    def motionDetected(self, home=None, camera=None, exclude=0):
        """
        Return True if movement has been detected
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            print("motionDetected: Camera name or home is unknown")
            return False

        if exclude:
            limit = (time.time() - exclude)
            array_time_event = sorted(self.events[cam_id])
            array_time_event.reverse()
            for time_ev in array_time_event:
                if time_ev < limit:
                    return False
                elif self.events[cam_id][time_ev]['type'] == 'movement':
                    return True
        elif self.lastEvent[cam_id]['type'] == 'movement':
            return True
        return False

    def outdoormotionDetected(self, home=None, camera=None, offset=0):
        """
        Return True if outdoor movement has been detected
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            print("outdoormotionDetected: Camera name or home is unknown")
            return False
        if self.lastEvent[cam_id]['type'] == 'movement':
            if self.lastEvent[cam_id]['video_status'] == 'recording' and\
             self.lastEvent[cam_id]['time'] + offset > int(time.time()):
                return True
        return False

    def humanDetected(self, home=None, camera=None, offset=0):
        """
        Return True if a human has been detected
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            print("personSeenByCamera: Camera name or home is unknown")
            return False
        if self.outdoor_lastEvent[cam_id]['video_status'] == 'recording':
            for e in self.outdoor_lastEvent[cam_id]['event_list']:
                if e['type'] ==\
                 'human' and e['time'] + offset > int(time.time()):
                    return True
        return False

    def animalDetected(self, home=None, camera=None, offset=0):
        """
        Return True if an animal has been detected
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            print("animalDetected: Camera name or home is unknown")
            return False

        if self.outdoor_lastEvent[cam_id]['video_status'] == 'recording':
            for e in self.outdoor_lastEvent[cam_id]['event_list']:
                if e['type'] ==\
                 'animal' and e['time'] + offset > int(time.time()):
                    return True
        return False

    def carDetected(self, home=None, camera=None, offset=0):
        """
        Return True if a car has been detected
        """
        try:
            cam_id = self.cameraByName(camera=camera, home=home)['id']
        except TypeError:
            print("carDetected: Camera name or home is unknown")
            return False

        if self.outdoor_lastEvent[cam_id]['video_status'] == 'recording':
            for e in self.outdoor_lastEvent[cam_id]['event_list']:
                if e['type'] ==\
                 'vehicle' and e['time'] + offset > int(time.time()):
                    return True
        return False

    def moduleMotionDetected(self, module=None, home=None,
                             camera=None, exclude=0):
        """
        Return True if movement has been detected
        """
        try:
            mod = self.moduleByName(module, camera=camera, home=home)
            mod_id = mod['id']
            cam_id = mod['cam_id']
        except TypeError:
            print("moduleMotionDetected: Module name or"
                  "Camera name or home is unknown")
            return False

        if exclude:
            limit = (time.time() - exclude)
            array_time_event = sorted(self.events[cam_id])
            array_time_event.reverse()
            for time_ev in array_time_event:
                if time_ev < limit:
                    return False
                elif (self.events[cam_id][time_ev]['type'] == 'tag_big_move'
                      or self.events[cam_id][time_ev]['type'] ==
                      'tag_small_move') and\
                        self.events[cam_id][time_ev]['module_id'] == mod_id:
                    return True
        elif (self.lastEvent[cam_id]['type'] == 'tag_big_move' or
              self.lastEvent[cam_id]['type'] == 'tag_small_move') and\
              self.lastEvent[cam_id]['module_id'] == mod_id:
                    return True
        return False

    def moduleOpened(self, module=None, home=None, camera=None, exclude=0):
        """
        Return True if module status is open
        """
        try:
            mod = self.moduleByName(module, camera=camera, home=home)
            mod_id = mod['id']
            cam_id = mod['cam_id']
        except TypeError:
            print("moduleOpened: Camera name, or home, or module is unknown")
            return False

        if exclude:
            limit = (time.time() - exclude)
            array_time_event = sorted(self.events[cam_id])
            array_time_event.reverse()
            for time_ev in array_time_event:
                if time_ev < limit:
                    return False
                elif self.events[cam_id][time_ev]['type'] == 'tag_open' and\
                     self.events[cam_id][time_ev]['module_id'] == mod_id:
                    return True
        elif self.lastEvent[cam_id]['type'] == 'tag_open' and\
             self.lastEvent[cam_id]['module_id'] == mod_id:
            return True
        return False
