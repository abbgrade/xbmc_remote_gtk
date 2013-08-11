'''
Created on 30.05.2013

@author: abb
'''
from gi.repository import Gtk as gtk  # @UnresolvedImport
from gi.repository import GObject as gobject  # @UnresolvedImport
from gi.repository import Notify as pynotify  # @UnresolvedImport
pynotify.init('XBMC Remote')
gobject.threads_init()
from os.path import abspath, dirname, join

import logging
logging = logging.getLogger(__name__)

from model import AudioPlayer as AudioPlayerModel
from model import Remote as RemoteModel

class PlayerWindow(object,
                   RemoteModel.ConnectionStateObserver,
                   AudioPlayerModel.CurrentSongObserver,
                   AudioPlayerModel.IsPlayingObserver):

    WIDGETS = ['player_window',
               'playlist_liststore',
               'genre_liststore',
               'artist_liststore',
               'album_liststore',
               'track_liststore',
               'song_title_label',
               'song_subtitle_label',
               'play_toolbutton',
               'pause_toolbutton',
               'song_progress_box',
               'volume_button',
               'player_statusbar']

    def __init__(self, core):
        logging.debug('init player window')
        self.core = core
        self.model = AudioPlayerModel()

        # init gui builder
        self.builder = gtk.Builder()
        glade_file = join(abspath(dirname(__file__)), 'player_window.glade')
        self.builder.add_from_file(glade_file)
        self.builder.connect_signals(self)

        # add widgets
        for widget_name in PlayerWindow.WIDGETS:
            widget = self.builder.get_object(widget_name)
            object.__setattr__(self, widget_name, widget)

        self.core.client.model.register_connection_state_observer(self)
        self.model.register_current_song_observer(self)
        self.model.register_is_playing_observer(self)

        self.player_window.show_all()
        self.song_progress_box.hide()
        self._update_window_state()

    def _update_window_state(self):
        context = self.player_statusbar.get_context_id(PlayerWindow.STATUSBAR_CONTEXT_CONNECTION)
        self.player_statusbar.push(context, RemoteModel.CONNECTION_STATES[self.core.client.model.connection_state])
        self.player_window.set_sensitive(self.core.client.model.connection_state == RemoteModel.CONNECTION_STATE_AUTHENTICATED)

    def on_genres_update(self, genres):
        for genre in self.core.client.audio_library.get_genres():
            self.genre_liststore.append([genre.label])

    def on_artists_update(self, artists):
        for artist in self.core.client.audio_library.get_artists():
            self.artist_liststore.append([artist.name])

    def on_albums_update(self, albums):
        for album in self.core.client.audio_library.get_albums():
            self.album_liststore.append([album.title])

    STATUSBAR_CONTEXT_CONNECTION = 'connection'

    def on_connection_state_update(self, state):
        self._update_window_state()

    def run(self):
        gtk.main()

    def quit(self):
        gtk.main_quit()

    def on_player_window_destroy(self, *args):
        logging.debug('close player window')
        self.core.quit()

    def on_play_toolbutton_clicked(self, *args):
        self.model.controller.toggle_play_pause()

    def on_pause_toolbutton_clicked(self, *args):
        self.model.controller.toggle_play_pause()

    def on_go_previous_toolbutton_clicked(self, *args):
        self.model.controller.go_previous()

    def on_next_toolbutton_clicked(self, *args):
        self.model.controller.go_next()

    def on_current_song_update(self, current_song):
        if current_song:
            self.song_title_label.set_text(current_song.title)
            self.song_subtitle_label.set_text(' - '.join([current_song.artist, current_song.album]))
        else:
            self.song_title_label.set_text('-')
            self.song_subtitle_label.set_text(' - '.join(['', '']))

    def on_is_playing_update(self, is_playing):
        if is_playing:
            self.play_toolbutton.hide()
            self.pause_toolbutton.show()
        else:
            self.play_toolbutton.show()
            self.pause_toolbutton.hide()

    def on_connection_edit_menuitem_activate(self, *args):
        config_dialog = ConfigDialog(self.core.config)
        config_dialog.run()


class ConfigDialog(object):

    WIDGETS = ['config_dialog',
               'hostname_entry',
               'port_entry',
               'username_entry',
               'password_entry']

    def __init__(self, config):
        logging.debug('init config dialog')
        self.model = config

        # init gui builder
        self.builder = gtk.Builder()
        glade_file = join(abspath(dirname(__file__)), 'config_dialog.glade')
        self.builder.add_from_file(glade_file)
        self.builder.connect_signals(self)

        # add widgets
        for widget_name in ConfigDialog.WIDGETS:
            widget = self.builder.get_object(widget_name)
            object.__setattr__(self, widget_name, widget)

        # sent content
        self.hostname_entry.set_text(self.model['server']['host'])
        self.port_entry.set_text(str(self.model['server']['port']))
        self.username_entry.set_text(self.model['server']['username'])
        self.password_entry.set_text(self.model['server']['password'])

        self.config_dialog.show_all()

    def run(self):
        logging.debug('run config dialog')
        return self.config_dialog.run()

    def quit(self):
        self.config_dialog.destroy()

    def on_config_dialog_close(self, *args):
        logging.debug('close config dialog')
        self.quit()

    def on_config_dialog_response(self, dialog, response_id):
        if response_id == -1 or response_id == -4:
            logging.debug('abort config dialog')
        elif response_id == 1:
            self.model['server']['host'] = self.hostname_entry.get_text()
            try:
                self.model['server']['port'] = int(self.port_entry.get_text())
            except: pass
            self.model['server']['username'] = self.username_entry.get_text()
            self.model['server']['password'] = self.password_entry.get_text()
            self.model.save()
        else:
            logging.debug('abort config dialog')
        self.quit()
