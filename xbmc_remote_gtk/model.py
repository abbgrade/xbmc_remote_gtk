'''
Created on 30.05.2013

@author: abb
'''

class Player(object):

    pass

class AudioPlayer(Player):

    def __init__(self, controller = None):
        self.controller = controller
        self._current_song = None
        self._speed = None
        self._current_song_observer = []
        self._is_playing_observer = []

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

    def register_is_playing_observer(self, observer):
        self._is_playing_observer.append(observer)
        observer.on_is_playing_update(self.is_playing)

    def notify_is_playing_observer(self):
        for observer in self._is_playing_observer:
            observer.on_is_playing_update(self.is_playing)

    def register_current_song_observer(self, observer):
        self._current_song_observer.append(observer)
        observer.on_current_song_update(self.current_song)

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
