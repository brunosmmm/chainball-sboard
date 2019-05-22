"""Game Exceptions."""


class GameAlreadyStarterError(Exception):
    """Game already started."""


class GameNotStartedError(Exception):
    """Game not started."""


class PlayerRemoteNotPaired(Exception):
    """Remote is not paired."""


class PlayerNotRegisteredError(Exception):
    """Player is not registered."""


class TooManyPlayersError(Exception):
    """Too many players registered."""


class NotEnoughPlayersError(Exception):
    """Not enough players registered."""


class PlayerAlreadyPairedError(Exception):
    """Player remote already paired."""


class PlayerNotPairedError(Exception):
    """Player remote is not paired."""


class GameRunningError(Exception):
    """Game is already running."""


class MasterRemoteAlreadyPairedError(Exception):
    """Master remote is already paired."""


class GameAlreadyPausedError(Exception):
    """Game is already paused."""


class GameNotPausedError(Exception):
    """Game is not paused."""


class ChainballGameError(Exception):
    """Game-related error"""
