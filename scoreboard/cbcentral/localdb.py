"""Local, simplified cache for remote databases."""

import json
import os
from logging import getLogger
from typing import List, Dict, Type

from scoreboard.cbcentral.queries import (
    query_games,
    query_players,
    query_tournaments,
    get_sfx_data,
)
from scoreboard.cbcentral.util import id_from_url, md5_sum
from scoreboard.util.configfiles import CHAINBALL_CONFIGURATION
from scoreboard.cbcentral.api import CBCentralAPIError
from scoreboard.util.soundfx import SFX_HANDLER

LOCALDB_LOGGER = getLogger("sboard.localdb")


class ChainBallLocalDBError(Exception):
    """Local DB error."""


class LocalRegistryEntry:
    """Local registry entry."""

    _index: str = None
    _fields: List[str] = []

    def __init__(self, **kwargs):
        """Initialize."""
        self._kwargs = kwargs

    @property
    def index(self):
        """Get index member value."""
        if self._index is not None:
            return getattr(self, self._index)

        return None

    @classmethod
    def get_index_name(cls) -> str:
        """Get index member name."""
        return cls._index

    @classmethod
    def get_field_names(cls) -> List[str]:
        """Get fields."""
        return cls._fields

    @property
    def serialized(self) -> Dict:
        """Get serialized."""
        serialized = {arg: getattr(self, arg) for arg in self._fields}
        serialized.update(self._kwargs)
        return serialized


class LocalRegistry:
    """Local registry."""

    def __init__(self, registry_name: str, entry_class: Type):
        """Initialize."""
        self._entry_class = entry_class
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

        # build
        self.build_registry(self._registry_contents)

    @property
    def serialized(self) -> List[Dict]:
        """Get serialized."""
        return [item.serialized for item in self._registry_contents]

    def update_registry(self):
        """Update registry."""
        raise NotImplementedError

    def build_registry(self, contents: List) -> None:
        """Build registry."""
        self._registry_contents = [
            self._entry_class(**item) for item in contents
        ]

    def commit_registry(self):
        """Commit to disk."""
        with open(self._registry_location, "w") as registry:
            json.dump(self.serialized, registry, indent=2)

    def __getitem__(self, item):
        if self._entry_class.get_index_name() is not None:
            for element in self._registry_contents:
                if element.index == item:
                    return element

        raise KeyError

    def __iter__(self):
        """Get iterator."""
        return iter(self._registry_contents)

    def __contains__(self, item):
        """Contains or not."""
        try:
            _ = self[item]
            return True
        except KeyError:
            return False

    @property
    def data_layout(self):
        """Get data layout."""
        return self._entry_class.get_field_names()


class PlayerEntry(LocalRegistryEntry):
    """Locally cached player description."""

    _index = "username"
    _fields = ["name", "display_name", "username", "sfx_md5"]

    def __init__(self, name, display_name, username, sfx_md5, **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
        self._name = name
        self._dispname = display_name
        self._username = username
        self._sfx_md5 = sfx_md5

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
    def sfx_md5(self):
        """Get sfx md5 sum."""
        return self._sfx_md5


class LocalPlayerRegistry(LocalRegistry):
    """Local player registry."""

    def __init__(self):
        super().__init__("player_registry", PlayerEntry)

        # build registry
        LOCALDB_LOGGER.info("local player registry loaded")

    def update_registry(self):
        """Update registry with information from central server."""
        LOCALDB_LOGGER.info("updating player registry from central server")
        upstream_players = query_players()
        self.build_registry(upstream_players)


class TournamentEntry(LocalRegistryEntry):
    """Tournament registry entry."""

    _index = "id"
    _fields = [
        "id",
        "season",
        "description",
        "event_date",
        "players",
        "status",
        "games",
    ]

    def __init__(
        self,
        id,
        season,
        description,
        event_date,
        players,
        status,
        games,
        **kwargs
    ):
        """Initialize."""
        super().__init__(**kwargs)
        self._id = id
        self._season = id_from_url(season)
        self._description = description
        self._date = event_date
        # abbreviate player data
        self._players = [id_from_url(player) for player in players]
        self._status = status
        # also abbreviate
        self._games = self._get_game_ids(games)

    @staticmethod
    def _get_game_ids(games):
        """Get game ids."""
        ret = []
        for game in games:
            if isinstance(game, int):
                ret.append(game)
            elif isinstance(game, str):
                ret.append(int(id_from_url(game)))
            else:
                raise TypeError("invalid type")

        return ret

    @property
    def id(self):
        """Get id."""
        return self._id

    @property
    def season(self):
        """Get season."""
        return self._season

    @property
    def description(self):
        """Get description."""
        return self._description

    @property
    def event_date(self):
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


class LocalTournamentRegistry(LocalRegistry):
    """Tournament registry retrieved from central server."""

    def __init__(self):
        """Initialize."""
        super().__init__("tournament_registry", TournamentEntry)
        LOCALDB_LOGGER.info("local tournament registry loaded")

    def update_registry(self):
        """Update registry."""
        LOCALDB_LOGGER.info("updating game registry from central server")
        upstream_tournaments = query_tournaments()
        self.build_registry(upstream_tournaments)


class GameEntry(LocalRegistryEntry):
    """Game registry entry."""

    _index = "identifier"
    _fields = [
        "identifier",
        "sequence",
        "description",
        "tournament",
        "events",
        "players",
        "duration",
        "start_time",
        "game_status",
    ]

    def __init__(
        self,
        identifier,
        sequence,
        description,
        tournament,
        events,
        players,
        duration,
        start_time,
        game_status,
        **kwargs
    ):
        """Initialize."""
        super().__init__(**kwargs)
        self._identifier = identifier
        self._sequence = sequence
        self._description = description
        self._tournament = self._get_tournament_id(tournament)
        self._events = events
        self._players = [id_from_url(player) for player in players]
        self._duration = duration
        self._start_time = start_time
        self._status = game_status

    @staticmethod
    def _get_tournament_id(tournament):
        """Get tournament id."""
        if isinstance(tournament, int):
            return tournament
        if isinstance(tournament, str):
            return int(id_from_url(tournament))

        raise TypeError("invalid type")

    @property
    def identifier(self):
        """Get identifier."""
        return self._identifier

    @property
    def sequence(self):
        """Get sequence number."""
        return self._sequence

    @property
    def description(self):
        """Get description."""
        return self._description

    @property
    def tournament(self):
        """Get tournament id."""
        return self._tournament

    @property
    def events(self):
        """Get events."""
        return self._events

    @property
    def players(self):
        """Get players."""
        return self._players

    @property
    def duration(self):
        """Get duration."""
        return self._duration

    @property
    def start_time(self):
        """Get start time."""
        return self._start_time

    @property
    def game_status(self):
        """Get status."""
        return self._status


class LocalGameRegistry(LocalRegistry):
    """Game registry retrieved from server."""

    def __init__(self):
        """Initialize."""
        super().__init__("game_registry", GameEntry)

    def update_registry(self):
        """Update registry."""
        upstream_games = query_games()
        self.build_registry(upstream_games)


PLAYER_REGISTRY = LocalPlayerRegistry()
TOURNAMENT_REGISTRY = LocalTournamentRegistry()
GAME_REGISTRY = LocalGameRegistry()


def update_all():
    """Update everything."""
    try:
        PLAYER_REGISTRY.update_registry()
        PLAYER_REGISTRY.commit_registry()
    except CBCentralAPIError:
        LOCALDB_LOGGER.warning("could not update player registry from server")

    # check SFX data
    for player in PLAYER_REGISTRY:
        if player.username not in SFX_HANDLER.fx_desc:
            # SFX data not available, retrieve
            try:
                data = get_sfx_data(player.username)
            except CBCentralAPIError:
                LOCALDB_LOGGER.error("failed to retrieve SFX data")
                continue
            if data["status"] != "ok":
                LOCALDB_LOGGER.error(
                    "could not retrieve SFX data for player {}".format(
                        player.username
                    )
                )
                continue

            # insert data
            if data["data"] is not None:
                SFX_HANDLER.insert_sfx_data(player.username, data["data"])
        else:
            # check md5sum
            fx_path = os.path.join(SFX_HANDLER.fx_data_path, player.username)
            try:
                md5sum = md5_sum(fx_path)
            except OSError:
                LOCALDB_LOGGER.warning("could not calculate SFX checksum")
                continue

            if md5sum != player.sfx_md5:
                # must update!
                LOCALDB_LOGGER.info(
                    "updating SFX data for user {}".format(player.username)
                )
                try:
                    data = get_sfx_data(player.username)
                except CBCentralAPIError:
                    LOCALDB_LOGGER.error("failed to retrieve SFX data")
                    continue

                if data["status"] != "ok":
                    LOCALDB_LOGGER.error(
                        "could not retrieve SFX data for player {}".format(
                            player.username
                        )
                    )
                    continue

                # FIXME cannot fully remove SFX data!
                if data["data"] is not None:
                    SFX_HANDLER.insert_sfx_data(player.username, data["data"])

    # save SFX configuration
    SFX_HANDLER.commit_sfx_data()

    try:
        TOURNAMENT_REGISTRY.update_registry()
        TOURNAMENT_REGISTRY.commit_registry()
    except CBCentralAPIError:
        LOCALDB_LOGGER.warning(
            "could not update tournament registry from server"
        )

    try:
        GAME_REGISTRY.update_registry()
        GAME_REGISTRY.commit_registry()
    except CBCentralAPIError:
        LOCALDB_LOGGER.warning("could not update game registry from server")
