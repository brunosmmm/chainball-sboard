"""Query information using central API."""

from scoreboard.cbcentral.api import central_api_get


def query_players():
    """Query registered players from central server."""
    return central_api_get(sub_api="registry", path="players")
