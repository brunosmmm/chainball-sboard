"""Control Spotify playback."""

import requests
from scoreboard.util.configfiles import CHAINBALL_CONFIGURATION


class SpotifyError(Exception):
    """Spotify communication error."""


def get_spotify_play_state():
    """Get current state."""

    spotify_token = CHAINBALL_CONFIGURATION.scoreboard.spotify_token
    try:
        ret = requests.get(
            "https://api.spotify.com/v1/me/player",
            headers={"Authorization": "Bearer {}".format(spotify_token)},
        )
    except ConnectionError:
        raise SpotifyError("request failed")

    if ret.status_code != 200:
        # failed
        raise SpotifyError("request failed")

    current_status = ret.json()
    is_playing = current_status.get("is_playing")

    if is_playing is None:
        return False

    return is_playing


def pause_spotify():
    """Pause playback."""

    spotify_token = CHAINBALL_CONFIGURATION.scoreboard.spotify_token
    try:
        ret = requests.get(
            "https://api.spotify.com/v1/me/player/pause",
            headers={"Authorization": "Bearer {}".format(spotify_token)},
        )
    except ConnectionError:
        raise SpotifyError("request failed")

    if ret.status_code != 204:
        raise SpotifyError("request failed")


def play_spotify():
    """Resume playback."""

    spotify_token = CHAINBALL_CONFIGURATION.scoreboard.spotify_token
    try:
        ret = requests.get(
            "https://api.spotify.com/v1/me/player/play",
            headers={"Authorization": "Bearer {}".format(spotify_token)},
        )
    except ConnectionError:
        raise SpotifyError("request failed")

    if ret.status_code != 204:
        raise SpotifyError("request failed")
