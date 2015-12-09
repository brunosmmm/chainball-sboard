class GameTurnActions(object):

    INCREASE_SCORE = 0
    DECREASE_SCORE = 1
    PASS_TURN = 2

class MasterRemoteActions(object):

    PAUSE_UNPAUSE_CLOCK = 0

class GameStates(object):

    IDLE = 0
    RUNNING = 1
    ERROR = 2
