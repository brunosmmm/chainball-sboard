"""Query information using central API."""

import requests
from requests.exceptions import ConnectionError, Timeout
import posixpath
from scoreboard.util.configfiles import CHAINBALL_CONFIGURATION


class CBCentralQueryError(Exception):
    """Query error."""


class CBCentralQueryFailed(CBCentralQueryError):
    """Query failure."""


class CBCentralQueryTimeout(CBCentralQueryError):
    """Query timeout."""


def _get_central_address():
    """Get central server address."""
    scoreboard_config = CHAINBALL_CONFIGURATION.retrieve_configuration(
        "scoreboard"
    )

    return (
        scoreboard_config["chainball_server"],
        scoreboard_config["chainball_server_token"],
    )


def _central_api_get(sub_api=None, path=None, timeout=10):
    """Make a request."""
    central_server_address, _ = _get_central_address()

    # do not use access token for now
    # build request
    get_url = central_server_address
    if sub_api is not None:
        get_url = posixpath.join(get_url, sub_api)

    if path is not None:
        get_url = posixpath.join(get_url, path)

    # perform request (blocking)
    try:
        result = requests.get(get_url, timeout=timeout)
    except Timeout:
        raise CBCentralQueryTimeout("query timed out.")
    except ConnectionError:
        raise CBCentralQueryFailed("query failed")
    if result.status_code != 200:
        raise CBCentralQueryError(
            "error querying central API: error {}".format(result.status_code)
        )
    return result.json()


def central_server_alive(timeout=1):
    """Check if server is alive."""
    central_server_address, _ = _get_central_address()

    try:
        requests.get(central_server_address, timeout=timeout)
    except (Timeout, ConnectionError):
        return False

    return True


def query_players():
    """Query registered players from central server."""
    return _central_api_get(sub_api="registry", path="players")
