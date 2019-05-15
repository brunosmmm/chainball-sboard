"""Server API access."""

import posixpath

import requests
from requests.exceptions import ConnectionError, Timeout

from scoreboard.util.configfiles import CHAINBALL_CONFIGURATION


class CBCentralAPIError(Exception):
    """API access error."""


class CBCentralAPITimeout(CBCentralAPIError):
    """Timeout."""


def get_central_address():
    """Get central server address."""
    scoreboard_config = CHAINBALL_CONFIGURATION.retrieve_configuration(
        "scoreboard"
    )

    return (
        scoreboard_config["chainball_server"],
        scoreboard_config["chainball_server_token"],
    )


def central_api_get(sub_api=None, path=None, timeout=10):
    """Make a GET request."""
    central_server_address, _ = get_central_address()

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
        raise CBCentralAPITimeout("GET timed out.")
    except ConnectionError:
        raise CBCentralAPIError("GET failed")
    if result.status_code != 200:
        raise CBCentralAPIError(
            "error querying central API: error {}".format(result.status_code)
        )
    return result.json()


def central_api_post(sub_api=None, path=None, timeout=10):
    """Make a POST request."""
    central_server_address, _ = get_central_address()
    get_url = central_server_address
    if sub_api is not None:
        get_url = posixpath.join(get_url, sub_api)

    if path is not None:
        get_url = posixpath.join(get_url, path)

    raise NotImplementedError


def central_server_alive(timeout=1):
    """Check if server is alive."""
    central_server_address, _ = get_central_address()

    try:
        requests.get(central_server_address, timeout=timeout)
    except (Timeout, ConnectionError):
        return False

    return True
