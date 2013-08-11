'''
Created on 30.05.2013

@author: abb
'''

import logging
logging = logging.getLogger(__name__)

class Player(object):

    pass


class Remote(object):

    CONNECTION_STATE_OFFLINE = 0
    CONNECTION_STATE_ONLINE = 1
    CONNECTION_STATE_AUTHENTICATED = 2
    CONNECTION_STATES = {
        CONNECTION_STATE_OFFLINE: 'offline',
        CONNECTION_STATE_ONLINE:'online',
        CONNECTION_STATE_AUTHENTICATED:'authenticated'
    }

    @property
    def connection_state(self):
        return self._connection_state

    @connection_state.setter
    def connection_state(self, value):
        assert value in Remote.CONNECTION_STATES.keys()
        self._connection_state = value
        logging.debug('Client connection state: %s' % Remote.CONNECTION_STATES[value])
        self.notify_connection_state_observer(value)

    class ConnectionStateObserver:

        def on_connection_state_update(self, state):
            logging.error('Remote.ConnectionStateObserver.on_connection_state_update not implemented')
            raise NotImplementedError()

    def __init__(self):
        self._connection_state = Remote.CONNECTION_STATE_OFFLINE
        self._connection_state_observer = []

    def register_connection_state_observer(self, observer):
        assert isinstance(observer, Remote.ConnectionStateObserver)
        self._connection_state_observer.append(observer)

    def notify_connection_state_observer(self, state):
        for observer in self._connection_state_observer:
            observer.on_connection_state_update(state)


class AudioPlayer(Player):

    def __init__(self, controller = None):
        self._controller = controller
        self._current_song = None
        self._speed = None
        self._current_song_observer = []
        self._is_playing_observer = []

    @property
    def controller(self):
        return self._controller

    @controller.setter
    def controller(self, value):
        self._controller = value
        self._controller.model = self
        logging.debug('set controller')

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, value):
        previous_speed = self._speed
        self._speed = value
        if previous_speed != value:
            self.notify_is_playing_observer()

    @property
    def is_playing(self):
        if self.speed is None:
            self.speed = self.controller.speed
        return bool(self.speed)

    class IsPlayingObserver:

        def on_is_playing_update(self, is_playing):
            raise NotImplementedError()

    def register_is_playing_observer(self, observer):
        assert isinstance(observer, AudioPlayer.IsPlayingObserver)
        self._is_playing_observer.append(observer)

    def notify_is_playing_observer(self):
        for observer in self._is_playing_observer:
            observer.on_is_playing_update(self.is_playing)

    class CurrentSongObserver:

        def on_current_song_update(self, current_song):
            raise NotImplementedError()

    def register_current_song_observer(self, observer):
        assert isinstance(observer, AudioPlayer.CurrentSongObserver)
        self._current_song_observer.append(observer)

    def _notify_current_song_observer(self):
        for observer in self._current_song_observer:
            observer.on_current_song_update(self.current_song)

    @property
    def current_song(self):
        if self._current_song is None:
            self.controller.get_current_song()
        return self._current_song

    @current_song.setter
    def current_song(self, value):
        previous_song = self._current_song
        self._current_song = value
        self._notify_current_song_observer()
        if previous_song != self._current_song:
            self.is_playing

class Item(object):

    pass

class Song(Item):

    PROPERTIES = ['title', 'artist', 'album', 'year', 'genre']

    def __init__(self, id = None, **properties):
        self.id = id

        for key in Song.PROPERTIES:
            self.__setattr__(key, None)
        for key, value in properties.items():
            if key in Song.PROPERTIES:
                if isinstance(value, list):
                    value = ','.join(value)
                assert isinstance(value, basestring) or isinstance(value, int), 'song property is no string or integer'
                self.__setattr__(key, value)

    @property
    def label(self):
        return ' - '.join([self.title, self.artist])

    def __str__(self):
        return self.label

class Genre(object):

    def __init__(self, genreid, label):
        self.genreid = genreid
        self.label = label

    def __str__(self):
        return self.label

class Artist(object):

    def __init__(self, artistid, artist, label):
        self.artistid = artistid
        self.name = artist

    def __str__(self):
        return self.name

class Album(object):

    def __init__(self, albumid, label):
        self.albumid = albumid
        self.title = label

    def __str__(self):
        return self.title
