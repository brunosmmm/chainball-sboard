"""Live updates."""

from scoreboard.cbcentral.api import central_api_post


def push_event(game_uuid, evt_type, evt_desc):
    """Push event to server."""
    pass


def game_start(game_uuid, game_time):
    """Start game."""
    pass


def game_end(game_uuid, reason, winner, running_time, remaining_time):
    """End game."""
    pass
