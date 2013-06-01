'''
Created on 30.05.2013

@author: abb
'''

import os
import urllib2
import json
import logging
import threading

from model import Song as SongModel, AudioPlayer as AudioPlayerModel
from model import Genre as GenreModel, Artist as ArtistModel, Album as AlbumModel
from view import PlayerWindow

class Config(dict):

    def __init__(self, path):
        self.path = path
        config_dir = os.sep.join(path.split(os.sep)[:-1])
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        dict.__init__(self)
        self.load()

    def __getitem__(self, key):
        if key not in self:
            if key == 'server':
                self[key] = {
                    'host': 'localhost',
                    'port': 80,
                    'username': '',
                    'password': ''
                }
        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        if key == 'server':
            value = ServerConfig(**value)
        return dict.__setitem__(self, key, value)

    def save(self):
        logging.debug('save config')
        parent_path = os.sep.join(self.path.split(os.sep)[:-1])
        if not os.path.exists(parent_path):
            os.makedirs(parent_path)
        with open(self.path, 'wb') as fd:
            json.dump(self, fd)

    def load(self):
        logging.debug('load config')
        if not os.path.isfile(self.path):
            return
        with open(self.path) as fd:
            struct = json.load(fd)
            for key, value in struct.iteritems():
                self[key] = value


class ServerConfig(dict):

    def __init__(self, **args):
        dict.__init__(self, **args)

        self._update_observer = []

    def register_update_observer(self, observer):
        self._update_observer.append(observer)

    def _notify_update_observer(self):
        for observer in self._update_observer:
            observer.on_server_config_update(self)

    def __setitem__(self, key, value):
        if value != self.get(key, False):
            logging.debug('server config changed (%s)' % key)
            dict.__setitem__(self, key, value)
            self._notify_update_observer()


class Core:

    def __init__(self, config):
        logging.debug('start core')
        self.config = config

        self.client = Client(config['server'])
        config['server'].register_update_observer(self.client)

        players = self.client.get_active_players()
        if len(players) > 0:
            player = players[0]
        else:
            player = AudioPlayerModel()
        self.player_window = PlayerWindow(self, player)

        self.player_status_cron = GetPlayerStatusCron(self, 5)
        self.player_status_cron.start()

        self.player_window.run()

    def quit(self):
        self.player_status_cron.stop()
        self.player_window.quit()


class _Cron:

    def __init__(self, core, interval):
        logging.debug('start cron')
        self.core = core
        self.interval = interval
        self._timer = None
        self._timer_lock = threading.Lock()

    def stop(self):
        logging.debug('stop cron')
        self._timer.cancel()
        self._timer_lock.acquire(False)
        self._timer_lock.release()

    def start(self):
        if self._timer_lock.acquire(False):
            logging.debug('cron job started (interval: %ds)' % self.interval)
            self._timer = threading.Timer(self.interval, self._do_job)
            self._timer.start()
        else:
            logging.debug('cron job is already started')


class GetPlayerStatusCron(_Cron):

    def _do_job(self):
        logging.debug('do cron job')
        self.core.player_window.model.controller.get_current_song()
        self._timer_lock.release()
        self.start()


class RemoteException(Exception):

    def __init__(self, message, code, data = None):
        self.code = code
        self.data = data
        Exception.__init__(self, message)


class Client:

    def __init__(self, config):
        self.config = config

        self.authenticate()

        self.audio_library = AudioLibrary(self)

    def authenticate(self):
        url = 'http://%s:%d/jsonrpc' % (self.config['host'], self.config['port'])

        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, self.config['username'], self.config['password'])
        urllib2.install_opener(urllib2.build_opener(urllib2.HTTPBasicAuthHandler(passman)))

    def _request(self, method, headers = {}, **params):
        for key, value in {'Accept':'application/json'}.items():
            if key not in headers:
                headers[key] = value

        data = {
            'jsonrpc': '2.0',
            'id': 0,
            'method': method,
            'params': params
        }

        url = 'http://%s:%d/jsonrpc?request' % (self.config['host'], self.config['port'])

        data = json.dumps(data)
        request = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(request)
        result_struct = json.load(response)
        if 'error' in result_struct:
            raise RemoteException(**result_struct['error'])
        return result_struct['result']

    def get_active_players(self):
        return [_Player.from_struct(self, struct).model
                    for struct in self._request('Player.GetActivePlayers')
                ]

class _Library(object):

    pass


class AudioLibrary(_Library):

    def __init__(self, client):
        self.client = client

    def get_song(self, id = None, **params):
        struct = self.client._request('AudioLibrary.GetSongDetails', songid = id, properties = SongModel.PROPERTIES)
        item = SongModel(*struct)
        return item

    def get_genres(self):
        genres = []
        for struct in self.client._request('AudioLibrary.GetGenres')['genres']:
            genres.append(GenreModel(**struct))
        return genres

    def get_artists(self):
        artists = []
        for struct in self.client._request('AudioLibrary.GetArtists')['artists']:
            artists.append(ArtistModel(**struct))
        return artists

    def get_albums(self):
        albums = []
        for struct in self.client._request('AudioLibrary.GetAlbums')['albums']:
            albums.append(AlbumModel(**struct))
        return albums

class _Player(object):

    @classmethod
    def from_struct(cls, client, struct):
        _type = struct.pop('type')
        if _type == 'audio':
            self = AudioPlayer(client, **struct)
        else:
            raise Exception('unknown player type')
        return self

class AudioPlayer(_Player):

    PROPERTIES = {'speed': int}

    def __init__(self, client, playerid = None):
        self.client = client
        self.playerid = playerid
        self.model = AudioPlayerModel(self)

    def __getattribute__(self, name):
        if name in AudioPlayer.PROPERTIES.keys():
            response = self.client._request('Player.GetProperties', playerid = self.playerid, properties = [name])[name]
            return AudioPlayer.PROPERTIES[name](response)
        else:
            return _Player.__getattribute__(self, name)

    def toggle_play_pause(self):
        self.model.speed = self.client._request('Player.PlayPause', playerid = self.playerid)['speed']

    def go_next(self):
        if self.client._request('Player.GoNext', playerid = self.playerid) == 'OK':
            return True
        else:
            return False

    def go_previous(self):
        if self.client._request('Player.GoPrevious', playerid = self.playerid) == 'OK':
            return True
        else:
            return False

    def get_current_song(self):
        struct = self.client._request('Player.GetItem', playerid = self.playerid, properties = SongModel.PROPERTIES)
        _type = struct['item'].pop('type')
        if _type == 'song':
            item = SongModel(**struct['item'])
            self.model.current_song = item
            return item
        else:
            raise Exception('unknown item type')
