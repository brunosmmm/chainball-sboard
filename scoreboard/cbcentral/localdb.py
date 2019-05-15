"""Local, simplified cache for remote databases."""

import json
import os

from scoreboard.util.configfiles import CHAINBALL_CONFIGURATION
from scoreboard.cbcentral.queries import query_players, query_tournaments
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


class LocalRegistry:
    """Local registry."""

    def __init__(self, registry_name):
        """Initialize."""
        db_config = CHAINBALL_CONFIGURATION.db
        self._registry_location = os.path.join(
            db_config.database_location, db_config[registry_name]
        )

        if not os.path.exists(self._registry_location):
            try:
                with open(self._registry_location, "w") as registry:
                    registry.write("[]")

            except OSError:
                raise ChainBallLocalDBError("cannot create registry")

        # load registry
        try:
            with open(self._registry_location, "r") as registry:
                self._registry_contents = json.load(registry)
        except (OSError, json.JSONDecodeError):
            raise ChainBallLocalDBError("cannot load registry.")

    @property
    def serialized(self):
        """Get serialized."""
        raise NotImplementedError

    def update_registry(self):
        """Update registry."""
        raise NotImplementedError

    def commit_registry(self):
        """Commit to disk."""
        with open(self._registry_location, "w") as registry:
            json.dump(self.serialized, registry)


class LocalPlayerRegistry(LocalRegistry):
    """Local player registry."""

    def __init__(self):
        super().__init__("player_registry")

        # build registry
        self._player_registry = [
            PlayerEntry(**player) for player in self._registry_contents
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
        LOCALDB_LOGGER.info("updating player registry from central server")
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


class TournamentEntry:
    """Tournament registry entry."""

    def __init__(self, season, description, event_date, players, status, games):
        """Initialize."""
        self._season = season
        self._description = description
        self._date = event_date
        # abbreviate player data
        self._players = [player.strip("/").split("/")[-1] for player in players]
        self._status = status
        # also abbreviate
        self._games = [int(game.strip("/").split("/")[-1]) for game in games]

    @property
    def season(self):
        """Get season."""
        return self._season

    @property
    def description(self):
        """Get description."""
        return self._description

    @property
    def date(self):
        """Get date."""
        return self._date

    @property
    def players(self):
        """Get Players."""
        return self._players

    @property
    def status(self):
        """Get status."""
        return self._status

    @property
    def games(self):
        """Get games."""
        return self._games

    @property
    def serialized(self):
        """Get serialized."""
        return {
            "season": self._season,
            "description": self._description,
            "event_date": self._date,
            "players": self._players,
            "status": self._status,
            "games": self._games,
        }


class LocalTournamentRegistry(LocalRegistry):
    """Game registry retrieved from central server."""

    def __init__(self):
        """Initialize."""
        super().__init__("tournament_registry")
        self._tournament_registry = [
            TournamentEntry(**tournament)
            for tournament in self._registry_contents
        ]
        LOCALDB_LOGGER.info("local tournament registry loaded")

    def update_registry(self):
        """Update registry."""
        LOCALDB_LOGGER.info("updating game registry from central server")
        upstream_tournaments = query_tournaments()
        self._tournament_registry = None
        self._tournament_registry = [
            TournamentEntry(**tournament) for tournament in upstream_tournaments
        ]

    @property
    def serialized(self):
        """Get serialized registry."""
        return [
            tournament.serialized for tournament in self._tournament_registry
        ]


PLAYER_REGISTRY = LocalPlayerRegistry()
TOURNAMENT_REGISTRY = LocalTournamentRegistry()
