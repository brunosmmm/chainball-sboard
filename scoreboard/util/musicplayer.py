"""Control music players."""


class MusicPlayer:
    """Music player."""

    @property
    def is_playing():
        """Get whether playing."""
        raise NotImplementedError

    def pause():
        """Pause."""
        raise NotImplementedError

    def play():
        """Play."""
        raise NotImplementedError


class MusicPlayerException(Exception):
    """Music player exception."""
