'''
Created on 30.05.2013

@author: Steffen Kampmann
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
from model import AudioLibrary as AudioLibraryModel

import thread

class PlayerWindow(object,
                   RemoteModel.ConnectionStateObserver,
                   AudioPlayerModel.CurrentSongObserver,
                   AudioPlayerModel.IsPlayingObserver):

    WIDGETS = ['player_window',
               'playlist_liststore',
               'genre_liststore',
               'genre_treeview',
               'artist_liststore',
               'artist_treeview',
               'album_liststore',
               'album_treeview',
               'track_liststore',
               'song_title_label',
               'song_subtitle_label',
               'play_toolbutton',
               'pause_toolbutton',
               'song_progress_box',
               'volume_button',
               'player_statusbar']

    def __init__(self, core, remote_model, library_model):
        logging.debug('init player window')
        assert isinstance(remote_model, RemoteModel)
        assert isinstance(library_model, AudioLibraryModel)

        self.core = core
        self.model = AudioPlayerModel()
        self.remote_model = remote_model
        self.library_model = library_model
        self._update_library_lock = thread.allocate_lock()

        # init gui builder
        self.builder = gtk.Builder()
        glade_file = join(abspath(dirname(__file__)), 'player_window.glade')
        self.builder.add_from_file(glade_file)
        self.builder.connect_signals(self)

        # add widgets
        for widget_name in PlayerWindow.WIDGETS:
            widget = self.builder.get_object(widget_name)
            object.__setattr__(self, widget_name, widget)

        self._all_genres = self.genre_liststore.prepend(['#alle Genres'])
        self._all_artists = self.artist_liststore.prepend(['#alle Kuenstler'])
        self._all_albums = self.album_liststore.prepend(['#alle Alben'])

        self.remote_model.register_connection_state_observer(self)
        self.model.register_current_song_observer(self)
        self.model.register_is_playing_observer(self)

        self.player_window.show_all()
        self.song_progress_box.hide()
        # self.genre_treeview.set_cursor(0)
        # self.artist_treeview.set_cursor(0)
        # self.album_treeview.set_cursor(0)

        self._update_window_state()
        self._update_library()

    def _update_window_state(self):
        context = self.player_statusbar.get_context_id(PlayerWindow.STATUSBAR_CONTEXT_CONNECTION)
        self.player_statusbar.push(context, RemoteModel.CONNECTION_STATES[self.remote_model.connection_state])
        self.player_window.set_sensitive(self.remote_model.connection_state == RemoteModel.CONNECTION_STATE_AUTHENTICATED)

    def _update_library(self):
        if self._update_library_lock.acquire(0):  # not more than one update
            logging.debug('update library')
            genre_selection = self._get_selection_from_listview(self.genre_treeview)
            artist_selection = self._get_selection_from_listview(self.artist_treeview)
            album_selection = self._get_selection_from_listview(self.album_treeview)

            genres, artists, albums = self.library_model.get_filter(genre_selection, artist_selection, album_selection)

            genre_labels = [genre.label for genre in genres]
            for row in self.genre_liststore:
                if row.iter == self._all_genres:
                    pass
                elif row[0] not in genre_labels:
                    self.genre_liststore.remove(row.iter)

            artist_names = [artist.name for artist in artists]
            for row in self.artist_liststore:
                if row.iter == self._all_artists:
                    pass
                elif row[0] not in artist_names:
                    self.artist_liststore.remove(row.iter)

            album_titles = [album.title for album in albums]
            for row in self.album_liststore:
                if row.iter == self._all_albums:
                    pass
                elif row[0] not in album_titles:
                    self.album_liststore.remove(row.iter)

            for genre in genres:
                already_inside = False
                for row in self.genre_liststore:
                    if row[0] == genre.label:
                        already_inside = True
                        break
                if not already_inside:
                    self.genre_liststore.append([genre.label])

            for artist in artists:
                already_inside = False
                for row in self.artist_liststore:
                    if row[0] == artist.name:
                        already_inside = True
                        break
                if not already_inside:
                    self.artist_liststore.append([artist.name])

            for album in albums:
                already_inside = False
                for row in self.album_liststore:
                    if row[0] == album.title:
                        already_inside = True
                        break
                if not already_inside:
                    self.album_liststore.append([album.title])

            self._update_library_lock.release()

    STATUSBAR_CONTEXT_CONNECTION = 'connection'

    def on_connection_state_update(self, state):
        self._update_window_state()

    def run(self):
        gtk.main()

    def quit(self):
        self._update_library_lock.acquire(0)
        gtk.main_quit()

    def on_player_window_destroy(self, *args):
        logging.debug('close player window')
        self._update_library_lock.acquire(0)
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

    def _get_selection_from_listview(self, list_view):
        selection = []
        if list_view.get_selection():
            model, pathlist = list_view.get_selection().get_selected_rows()
            all_path = None
            if len(pathlist) > 0:
                all_path = model.get_path(model.get_iter_from_string('0'))
            if all_path in pathlist:
                pass  # all means nothing in particular
            else:
                for path in pathlist:
                    tree_iter = model.get_iter(path)
                    selection.append(model.get_value(tree_iter, 0))
        return selection

    def on_genre_treeview_cursor_changed(self, tree_view):
        self._update_library()

    def on_artist_treeview_cursor_changed(self, tree_view):
        self._update_library()

    def on_album_treeview_cursor_changed(self, tree_view):
        self._update_library()


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
