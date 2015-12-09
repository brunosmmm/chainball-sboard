PLAYER_SERVE_SCORE_TIMEOUT = 3

class PlayerScoreCommands(object):

    CLR = 1
    SCORE = 2
    TURN = 3
    MODE = 4
    DATA = 5
    BLINK = 6
    TERM = 0xFF

class PlayerScoreConstraints(object):

    LARGE_TEXT_MAX_LEN = 7
    SMALL_TEXT_MAX_LEN = 20

class PlayerServeStates(object):
    IDLE = 0
    SERVING = 1
    SCORED = 2
    FINISHED = 3
