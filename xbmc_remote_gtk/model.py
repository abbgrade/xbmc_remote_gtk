'''
Created on 30.05.2013

@author: Steffen Kampmann
'''

import logging
logging = logging.getLogger(__name__)

import json

class AudioLibrary(object):

    def __init__(self, controller):
        self.controller = controller

        self.genres, self.artists, self.albums = [], [], []

        self._previous_selection = None

#         self.on_genres_update()
#         self.on_artists_update()
#         self.on_albums_update()

    def get_filter(self, genre_selection, artist_selection, album_selection):
        if self._previous_selection != json.dumps((genre_selection, artist_selection, album_selection)):
            self._previous_selection = json.dumps((genre_selection, artist_selection, album_selection))

            logging.debug('select ' + ', '.join(genre_selection) + ', '.join(artist_selection) + ', '.join(album_selection))

            genre_ids = []
            for genre in self.genres:
                if genre.label in genre_selection:
                    genre_selection.remove(genre.label)
                    genre_ids.append(genre.genreid)

            artist_ids = []
            for artist in self.artists:
                if artist.name in artist_selection:
                    artist_selection.remove(artist.name)
                    artist_ids.append(artist.artistid)

            album_ids = []
            for album in self.albums:
                if album.title in self.albums:
                    album_selection.remove(album.title)
                    album_ids.append(album.albumid)

            self.genres, self.artists, self.albums = [], [], []

            for genre in self.controller.get_genres():
                self.genres.append(genre)

            for artist in self.controller.get_artists(genres = genre_ids):
                self.artists.append(artist)

            for album in self.controller.get_albums(artists = artist_ids):
                self.albums.append(album)

        return self.genres, self.artists, self.albums

#     def on_genres_update(self):
#         for genre in self.controller.get_genres():
#             self.genres.append([genre.label])
#
#     def on_artists_update(self):
#         for artist in self.controller.get_artists():
#             self.artists.append([artist.name])
#
#     def on_albums_update(self):
#         for album in self.controller.get_albums():
#             self.albums.append([album.title])

class Player(object):

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

    def __init__(self):
        self._speed = None
        self._is_playing_observer = []


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
        Player.__init__(self)
        self._controller = controller
        self._current_song = None
        self._current_song_observer = []

    @property
    def controller(self):
        return self._controller

    @controller.setter
    def controller(self, value):
        self._controller = value
        self._controller.model = self
        logging.debug('set controller')

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
