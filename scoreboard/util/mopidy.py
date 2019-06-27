"""Control local mopidy."""

import requests
import json


class MopidyError(Exception):
    """Mopidy control error."""


def mopidy_pause():
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
    except ConnectionError:
        raise MopidyError("request failed")

    if ret.status_code != 200:
        raise MopidyError("request failed")


def mopidy_play():
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
    except ConnectionError:
        raise MopidyError("request failed")

    if ret.status_code != 200:
        raise MopidyError("request failed")
