"""Query information using central API."""

import scoreboard.cbcentral.api as api


def query_players():
    """Query registered players from central server."""
    return api.ChainballCentralAPI.central_api_get(
        sub_api="api", path="players"
    )


def query_tournaments():
    """Query tournaments."""
    return api.ChainballCentralAPI.central_api_get(
        sub_api="api", path="tournaments"
    )


def query_games():
    """Query games."""
    return api.ChainballCentralAPI.central_api_get(sub_api="api", path="games")


def query_announcements():
    """Query announcements."""
    return api.ChainballCentralAPI.central_api_get(
        sub_api="api", path="announce"
    )


def get_sfx_data(player):
    """Get player SFX data."""
    return api.ChainballCentralAPI.central_api_get(
        sub_api="api", path=f"players/{player}/get_sfx_data"
    )
