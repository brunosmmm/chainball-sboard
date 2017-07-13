"""Score constants."""

PLAYER_SERVE_SCORE_TIMEOUT = 3


class PlayerScoreCommands(object):
    """Score display commands."""

    CLR = 1
    SCORE = 2
    TURN = 3
    MODE = 4
    DATA = 5
    BLINK = 6
    TERM = 0xFF


class PlayerScoreConstraints(object):
    """Score text constraints."""

    LARGE_TEXT_MAX_LEN = 7
    SMALL_TEXT_MAX_LEN = 20


class PlayerServeStates(object):
    """Serve states."""

    IDLE = 0
    SERVING = 1
    SCORED = 2
    FINISHED = 3
