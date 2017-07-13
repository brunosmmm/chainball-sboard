"""Game Exceptions."""


class GameAlreadyStarterError(Exception):
    """Game already started."""

    pass


class GameNotStartedError(Exception):
    """Game not started."""

    pass


class PlayerRemoteNotPaired(Exception):
    """Remote is not paired."""

    pass


class PlayerNotRegisteredError(Exception):
    """Player is not registered."""

    pass


class TooManyPlayersError(Exception):
    """Too many players registered."""

    pass


class NotEnoughPlayersError(Exception):
    """Not enough players registered."""

    pass


class PlayerAlreadyPairedError(Exception):
    """Player remote already paired."""

    pass


class PlayerNotPairedError(Exception):
    """Player remote is not paired."""

    pass


class GameRunningError(Exception):
    """Game is already running."""

    pass


class MasterRemoteAlreadyPairedError(Exception):
    """Master remote is already paired."""

    pass


class GameAlreadyPausedError(Exception):
    """Game is already paused."""

    pass


class GameNotPausedError(Exception):
    """Game is not paused."""

    pass
