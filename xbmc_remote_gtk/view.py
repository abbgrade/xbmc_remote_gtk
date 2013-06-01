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

from model import AudioPlayer as AudioPlayerModel

class PlayerWindow(object):

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
               'volume_button']

    def __init__(self, core, player):
        logging.debug('init player window')

        assert isinstance(player, AudioPlayerModel)

        self.core = core
        self.model = player

        # init gui builder
        self.builder = gtk.Builder()
        glade_file = join(abspath(dirname(__file__)), 'player_window.glade')
        self.builder.add_from_file(glade_file)
        self.builder.connect_signals(self)

        # add widgets
        for widget_name in PlayerWindow.WIDGETS:
            widget = self.builder.get_object(widget_name)
            object.__setattr__(self, widget_name, widget)

        self.player_window.show_all()
        self.song_progress_box.hide()

        self.model.register_current_song_observer(self)
        self.model.register_is_playing_observer(self)

        for genre in self.core.client.audio_library.get_genres():
            self.genre_liststore.append([genre.label])

        for artist in self.core.client.audio_library.get_artists():
            self.artist_liststore.append([artist.name])

        for album in self.core.client.audio_library.get_albums():
            self.album_liststore.append([album.title])

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
        self.player.go_previous()

    def on_next_toolbutton_clicked(self, *args):
        self.player.go_next()

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
