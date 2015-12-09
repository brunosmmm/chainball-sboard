#remote pairing
class RemotePairStates(object):

    IDLE = 0
    RUNNING = 1
    ERROR = 2

class RemotePairFailureType(object):
    OK = 0
    TIMEOUT = 1
    ALREADY_PAIRED = 2

PAIRING_TIMEOUT = 30

class RemoteCommands(object):

    BTN_PRESS = 2
    BTN_RELEASE = 1
    BATT = 3
