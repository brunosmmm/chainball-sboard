"""Local, simplified cache for remote databases."""

import json
import os

from scoreboard.util.configfiles import CHAINBALL_CONFIGURATION
from scoreboard.cbcentral.queries import query_players
from logging import getLogger


LOCALDB_LOGGER = getLogger("sboard.localdb")


class ChainBallLocalDBError(Exception):
    """Local DB error."""


class PlayerEntry:
    """Locally cached player description."""

    def __init__(self, name, display_name, username, sfx=None):
        """Initialize."""
        self._name = name
        self._dispname = display_name
        self._username = username
        self._sfx = sfx

    @property
    def name(self):
        """Get name."""
        return self._name

    @property
    def display_name(self):
        """Get display name."""
        return self._dispname

    @property
    def username(self):
        """Get username."""
        return self._username

    @property
    def serialized(self):
        """Serialized."""
        return {
            "name": self._name,
            "display_name": self._dispname,
            "username": self._username,
        }


class LocalPlayerRegistry:
    """Local player registry."""

    def __init__(self):
        """Initialize."""
        db_config = CHAINBALL_CONFIGURATION.retrieve_configuration("db")
        self._registry_location = os.path.join(
            db_config["database_location"], db_config["player_registry"]
        )

        # load registry
        try:
            with open(self._registry_location, "r") as registry:
                registry_contents = json.load(registry)
        except (OSError, json.JSONDecodeError):
            raise ChainBallLocalDBError("cannot load player registry.")

        # build registry
        self._player_registry = [
            PlayerEntry(**player) for player in registry_contents
        ]
        LOCALDB_LOGGER.info("local player registry loaded")

    def get_player_by_username(self, username):
        """Get player by username."""
        for player in self._player_registry:
            if player.username == username:
                return player

        return None

    @property
    def players(self):
        """Get list of all players in registry."""
        return self._player_registry

    def update_registry(self):
        """Update registry with information from central server."""
        LOCALDB_LOGGER.info("updating registry from central server")
        upstream_players = query_players()
        # for now just replace everything
        self._player_registry = None
        self._player_registry = [
            PlayerEntry(**player) for player in upstream_players
        ]

    @property
    def serialized(self):
        """Get serialized registry."""
        return [player.serialized for player in self._player_registry]

    def commit_registry(self):
        """Commit to disk."""
        LOCALDB_LOGGER.info("commiting registry to disk.")
        with open(self._registry_location, "w") as registry:
            json.dump(self.serialized, registry)


PLAYER_REGISTRY = LocalPlayerRegistry()
