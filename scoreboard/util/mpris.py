"""Control local music player using MPRIS."""

from scoreboard.util.musicplayer import MusicPlayer


class LocalPlayer(MusicPlayer):
    """Local player."""

    @property
    def is_playing():
        """Check if playing."""

    def pause():
        """Pause."""

    def play():
        """Play."""
