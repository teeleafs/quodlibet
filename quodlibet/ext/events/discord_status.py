# discord_status: Set Discord status as current song.
#
# Copyright (c) 2022 Aditi K <105543244+teeleafs@users.noreply.github.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from quodlibet import _, app
from quodlibet.plugins.events import EventPlugin
from quodlibet.pattern import Pattern
from quodlibet import config

from gi.repository import Gtk

try:
    from pypresence import Presence, InvalidID
except ImportError:
    from quodlibet.plugins import MissingModulePluginException
    raise MissingModulePluginException("pypresence")

# The below resources are from/uploaded-to the Discord Application portal.
QL_DISCORD_RP_ID = '974521025356242984'
QL_LARGE_IMAGE = "io-github-quodlibet-quodlibet"

VERSION = "1.0"


class DiscordStatusMessage(EventPlugin):
    PLUGIN_ID = _("Discord status message")
    PLUGIN_NAME = _("Discord Status Message")
    PLUGIN_DESC = _("Change your Discord status message according to what "
                    "you're currently listening to.")
    VERSION = VERSION

    c_rp_line1 = __name__ + "_rp_line1"
    c_rp_line2 = __name__ + "_rp_line2"

    def __init__(self):
        self.song = None
        self.discordrp = None

        try:
            self.rp_line1 = config.get('plugins', self.c_rp_line1)
            self.rp_line2 = config.get('plugins', self.c_rp_line2)
        except:
            self.rp_line1 = "<artist> / <title>"
            self.rp_line2 = "<album>"
            config.set('plugins', self.c_rp_line1, self.rp_line1)
            config.set('plugins', self.c_rp_line2, self.rp_line2)

    def update_discordrp(self, details, state=None):
        if not self.discordrp:
            try:
                self.discordrp = Presence(QL_DISCORD_RP_ID, pipe=0)
                self.discordrp.connect()
            except ConnectionRefusedError:
                self.discordrp = None

        if self.discordrp:
            try:
                self.discordrp.update(details=details, state=state,
                                large_image=QL_LARGE_IMAGE)
            except InvalidID:
                # XXX Discord was closed?
                self.discordrp = None

    def handle_play(self):
        if self.song:
            details = Pattern(self.rp_line1) % self.song
            state = Pattern(self.rp_line2) % self.song

            # The details and state fields must be atleast 2 characters.
            if len(details) < 2:
                details = None

            if len(state) < 2:
                state = None

            self.update_discordrp(details, state)

    def handle_paused(self):
        self.update_discordrp(details=_("Paused"))

    def handle_unpaused(self):
        if not self.song:
            self.song = app.player.song
        self.handle_play()

    def plugin_on_song_started(self, song):
        self.song = song
        if not app.player.paused:
            self.handle_play()

    def plugin_on_paused(self):
        self.handle_paused()

    def plugin_on_unpaused(self):
        self.handle_unpaused()

    def enabled(self):
        if app.player.paused:
            self.handle_paused()
        else:
            self.handle_unpaused()

    def disabled(self):
        if self.discordrp:
            self.discordrp.clear()
            self.discordrp.close()
            self.discordrp = None
            self.song = None

    def rp_line1_changed(self, entry):
        self.rp_line1 = entry.get_text()
        config.set('plugins', self.c_rp_line1, self.rp_line1)
        if not app.player.paused:
            self.handle_play()

    def rp_line2_changed(self, entry):
        self.rp_line2 = entry.get_text()
        config.set('plugins', self.c_rp_line2, self.rp_line2)
        if not app.player.paused:
            self.handle_play()

    def PluginPreferences(self, parent):
        vb = Gtk.VBox(spacing=6)

        status_line1_box = Gtk.HBox(spacing=6)
        status_line1_box.set_border_width(3)

        status_line1 = Gtk.Entry()
        status_line1.set_text(self.rp_line1)
        status_line1.connect('changed', self.rp_line1_changed)

        status_line1_box.pack_start(Gtk.Label(label=_("Status Line #1")),
                                        False, True, 0)
        status_line1_box.pack_start(status_line1, True, True, 0)

        status_line2_box = Gtk.HBox(spacing=3)
        status_line2_box.set_border_width(3)

        status_line2 = Gtk.Entry()
        status_line2.set_text(self.rp_line2)
        status_line2.connect('changed', self.rp_line2_changed)

        status_line2_box.pack_start(Gtk.Label(label=_('Status Line #2')),
                                        False, True, 0)
        status_line2_box.pack_start(status_line2, True, True, 0)

        vb.pack_start(status_line1_box, True, True, 0)
        vb.pack_start(status_line2_box, True, True, 0)

        return vb