"""Central server access utilities."""

from scoreboard.cbcentral.api import (
    central_api_get,
    central_api_post,
    CBCentralAPIError,
)
from scoreboard.cbcentral.localdb import (
    PLAYER_REGISTRY,
    TOURNAMENT_REGISTRY,
    GAME_REGISTRY,
)

import logging

logger = logging.getLogger("sboard.cbcentral")


def id_from_url(url):
    """Get player id from URL."""
    return url.strip("/").split("/")[-1]


def update_all():
    try:
        PLAYER_REGISTRY.update_registry()
        PLAYER_REGISTRY.commit_registry()
    except CBCentralAPIError:
        logger.warning("could not update player registry from server")

    try:
        TOURNAMENT_REGISTRY.update_registry()
        TOURNAMENT_REGISTRY.commit_registry()
    except CBCentralAPIError:
        logger.warning("could not update tournament registry from server")

    try:
        GAME_REGISTRY.update_registry()
        GAME_REGISTRY.commit_registry()
    except CBCentralAPIError:
        logger.warning("could not update game registry from server")
