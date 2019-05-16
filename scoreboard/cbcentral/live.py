"""Live updates."""

import logging

from scoreboard.cbcentral.api import (
    central_api_post,
    CBCentralAPIError,
    CBCentralAPITimeout,
)

_LOGGER = logging.getLogger("sboard.live")


def push_event(game_uuid, evt_type, evt_desc):
    """Push event to server."""
    post_data = {"evt_type": evt_type, "evt_data": evt_desc}
    try:
        result = central_api_post(
            post_data, sub_api="api", path=f"games/{game_uuid}/push_event"
        )
    except CBCentralAPIError as ex:
        _LOGGER.error("could not push event")

    if "status" not in result or result["status"] != "ok":
        _LOGGER.error("push_event request failed")


def game_start(game_uuid, start_time, player_order):
    """Start game."""
    order = ",".join(player_order)
    post_data = {"start_time": start_time, "player_order": order}
    try:
        result = central_api_post(
            post_data, sub_api="api", path=f"games/{game_uuid}/start_game"
        )
    except CBCentralAPIError as ex:
        _LOGGER.error("could not start game")

    if "status" not in result or result["status"] != "ok":
        _LOGGER.error("game_start request failed")


def game_end(game_uuid, reason, winner, running_time, remaining_time):
    """End game."""
    post_data = {
        "reason": start_time,
        "winner": winner,
        "running_time": running_time,
        "remaining_time": remaining_time,
    }
    try:
        result = central_api_post(
            post_data, sub_api="api", path=f"games/{game_uuid}/stop_game"
        )
    except CBCentralAPIError as ex:
        _LOGGER.error("could not stop game")

    if "status" not in result or result["status"] != "ok":
        _LOGGER.error("game_stop request failed")
