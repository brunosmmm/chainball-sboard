"""Server API access."""

import posixpath
import time
from collections import deque

import requests
from requests.exceptions import ConnectionError, Timeout

import scoreboard.cbcentral.localdb as localdb
from scoreboard.util.configfiles import CHAINBALL_CONFIGURATION
from scoreboard.util.threads import StoppableThread


class CBCentralAPIError(Exception):
    """API access error."""


class CBCentralAPITimeout(CBCentralAPIError):
    """Timeout."""


class ChainballCentralAPI(StoppableThread):
    """Central API."""

    def __init__(self):
        """Initialize."""
        super().__init__()
        self._outgoing_queue = deque()

    def run(self):
        """Run."""
        while not self.is_stopped():
            # update game registry to track tournament progress
            try:
                localdb.ANNOUNCE_REGISTRY.update_registry()
                localdb.GAME_REGISTRY.update_registry()
                localdb.GAME_REGISTRY.commit_registry()
            except CBCentralAPIError:
                pass
            while not self.is_stopped():
                # drop everything
                try:
                    data, sub_api, path, retry = self._outgoing_queue.popleft()
                    result = self._central_api_post(
                        data=data, sub_api=sub_api, path=path
                    )
                    if "status" not in result or result["status"] != "ok":
                        raise CBCentralAPIError()
                except IndexError:
                    break
                except (CBCentralAPITimeout, CBCentralAPIError):
                    # retry
                    if retry:
                        self._outgoing_queue.appendleft(
                            (data, sub_api, path, True)
                        )

                time.sleep(1)
            time.sleep(1)

    @staticmethod
    def get_central_address():
        """Get central server address."""
        scoreboard_config = CHAINBALL_CONFIGURATION.retrieve_configuration(
            "scoreboard"
        )

        return (
            scoreboard_config["chainball_server"],
            scoreboard_config["chainball_server_token"],
        )

    @classmethod
    def central_api_get(cls, sub_api=None, path=None, timeout=10):
        """Make a GET request."""
        central_server_address, api_key = cls.get_central_address()
        if not central_server_address:
            raise CBCentralAPIError("server address empty")

        # do not use access token for now
        # build request
        get_url = central_server_address
        if sub_api is not None:
            get_url = posixpath.join(get_url, sub_api)

        if path is not None:
            get_url = posixpath.join(get_url, path)

        # perform request (blocking)
        try:
            result = requests.get(
                get_url,
                timeout=timeout,
                headers={"Authorization": f"Api-Key {api_key}"},
                verify=False,
            )
        except Timeout:
            raise CBCentralAPITimeout("GET timed out.")
        except ConnectionError:
            raise CBCentralAPIError("GET failed")
        if result.status_code != 200:
            raise CBCentralAPIError(
                "error querying central API: error {}".format(
                    result.status_code
                )
            )
        return result.json()

    def push_post_request(self, data, sub_api=None, path=None, retry=True):
        """Push post request into queue."""
        self._outgoing_queue.append((data, sub_api, path, retry))

    def _central_api_post(self, data, sub_api=None, path=None, timeout=10):
        """Make a POST request."""
        central_server_address, api_key = self.get_central_address()
        if not central_server_address:
            raise CBCentralAPIError("server address empty")
        get_url = central_server_address
        if sub_api is not None:
            get_url = posixpath.join(get_url, sub_api)

        if path is not None:
            get_url = posixpath.join(get_url, path)

        try:
            result = requests.post(
                get_url,
                timeout=timeout,
                headers={"Authorization": f"Api-Key {api_key}"},
                data=data,
            )
        except Timeout:
            raise CBCentralAPITimeout("POST timed out")
        except ConnectionError:
            raise CBCentralAPIError("POST failed")

        if result.status_code != 200:
            raise CBCentralAPIError(
                "error while doing POST: error {}".format(result.status_code)
            )

        return result.json()

    @classmethod
    def central_server_alive(cls, timeout=1):
        """Check if server is alive."""
        central_server_address, _ = cls.get_central_address()

        try:
            requests.get(central_server_address, timeout=timeout, verify=False)
        except (Timeout, ConnectionError):
            return False

        return True


CENTRAL_API = ChainballCentralAPI()
