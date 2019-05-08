"""Constants."""


class GameTurnActions:
    """Possile actions."""

    INCREASE_SCORE = 0
    DECREASE_SCORE = 1
    PASS_TURN = 2


class MasterRemoteActions:
    """Master remote actions."""

    PAUSE_UNPAUSE_CLOCK = 0


class GameStates:
    """Game states."""

    IDLE = 0
    RUNNING = 1
    ERROR = 2
