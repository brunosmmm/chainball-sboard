"""Query information using central API."""

from scoreboard.cbcentral.api import ChainballCentralAPI


def query_players():
    """Query registered players from central server."""
    return ChainballCentralAPI.central_api_get(sub_api="api", path="players")


def query_tournaments():
    """Query tournaments."""
    return ChainballCentralAPI.central_api_get(
        sub_api="api", path="tournaments"
    )


def query_games():
    """Query games."""
    return ChainballCentralAPI.central_api_get(sub_api="api", path="games")


def get_sfx_data(player):
    """Get player SFX data."""
    return ChainballCentralAPI.central_api_get(
        sub_api="api", path=f"players/{player}/get_sfx_data"
    )
