"""Control local mopidy."""

from scoreboard.util.musicplayer import MusicPlayer, MusicPlayerException
import requests
import json


class MopidyError(MusicPlayerException):
    """Mopidy control error."""


class MopidyPlayer(MusicPlayer):
    """Mopidy music player."""

    @property
    def is_playing():
        """Check if currently playing."""
        json_data = {
            "method": "core.playback.get_state",
            "jsonrpc": "2.0",
            "prams": {},
            "id": 1,
        }
        payload = json.dumps(json_data)

        try:
            ret = requests.post(
                "http://127.0.0.1:6680/mopidy/rpc",
                headers={"Content-Type": "application/json"},
                data=payload,
            )
        except requests.exceptions.ConnectionError:
            raise MopidyError("request failed")
        except Exception:
            raise MopidyError("unknown error")

        if ret.status_code != 200:
            raise MopidyError("request failed")

        return ret.json()["result"] == "playing"

    def pause():
        """Play."""
        json_data = {
            "method": "core.playback.pause",
            "jsonrpc": "2.0",
            "prams": {},
            "id": 1,
        }
        payload = json.dumps(json_data)

        try:
            ret = requests.post(
                "http://127.0.0.1:6680/mopidy/rpc",
                headers={"Content-Type": "application/json"},
                data=payload,
            )
        except requests.exceptions.ConnectionError:
            raise MopidyError("request failed")
        except Exception:
            raise MopidyError("unknown error")

        if ret.status_code != 200:
            raise MopidyError("request failed")

    def play():
        """Play."""
        json_data = {
            "method": "core.playback.play",
            "jsonrpc": "2.0",
            "prams": {"tl_track": None, "tlid": None},
            "id": 1,
        }
        payload = json.dumps(json_data)

        try:
            ret = requests.post(
                "http://127.0.0.1:6680/mopidy/rpc",
                headers={"Content-Type": "application/json"},
                data=payload,
            )
        except requests.exceptions.ConnectionError:
            raise MopidyError("request failed")
        except Exception:
            raise MopidyError("unknown error")

        if ret.status_code != 200:
            raise MopidyError("request failed")
