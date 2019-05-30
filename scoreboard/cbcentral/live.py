"""Live updates."""

import logging
import json

from scoreboard.cbcentral.api import CENTRAL_API

_LOGGER = logging.getLogger("sboard.live")


def push_event(game_uuid, evt_type, evt_desc):
    """Push event to server."""
    post_data = {"evt_type": evt_type, "evt_data": evt_desc}
    data_dump = {"payload": json.dumps(post_data)}
    CENTRAL_API.push_post_request(
        data_dump, sub_api="api", path=f"games/{game_uuid}/push_event/"
    )


def game_start(game_uuid, start_time, player_order):
    """Start game."""
    order = ",".join(player_order)
    post_data = {"start_time": start_time, "player_order": order}
    data_dump = {"payload": json.dumps(post_data)}
    CENTRAL_API.push_post_request(
        data_dump, sub_api="api", path=f"games/{game_uuid}/start_game/"
    )


def game_end(game_uuid, reason, winner, running_time, remaining_time):
    """End game."""
    post_data = {
        "reason": reason,
        "winner": winner,
        "running_time": running_time,
        "remaining_time": remaining_time,
    }
    data_dump = {"payload": json.dumps(post_data)}
    CENTRAL_API.push_post_request(
        data_dump, sub_api="api", path=f"games/{game_uuid}/stop_game/"
    )
