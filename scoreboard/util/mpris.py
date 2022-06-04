"""Control local music player using MPRIS."""

import dbus
from scoreboard.util.musicplayer import MusicPlayer


class LocalPlayer(MusicPlayer):
    """Local player."""

    def __init__(self):
        """Initialize."""
        bus = dbus.SessionBus()
        self.proxy = bus.get_object(
            "org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2"
        )
        self.player = dbus.Interface(
            self.proxy, dbus_interface="org.mpris.MediaPlayer2.Player"
        )
        self.properties = dbus.Interface(
            self.proxy, dbus_interface="org.freedesktop.DBus.Properties"
        )

    @property
    def is_playing(self):
        """Check if playing."""
        return (
            self.properties.Get(
                "org.mpris.MediaPlayer2.Player", "PlaybackStatus"
            )
            == "Playing"
        )

    def pause(self):
        """Pause."""
        self.player.Pause()

    def play(self):
        """Play."""
        self.player.Play()
