"""Constants."""


class GameTurnActions(object):
    """Possile actions."""

    INCREASE_SCORE = 0
    DECREASE_SCORE = 1
    PASS_TURN = 2


class MasterRemoteActions(object):
    """Master remote actions."""

    PAUSE_UNPAUSE_CLOCK = 0


class GameStates(object):
    """Game states."""

    IDLE = 0
    RUNNING = 1
    ERROR = 2
