class GameAlreadyStarterError(Exception):
    pass

class GameNotStartedError(Exception):
    pass

class PlayerRemoteNotPaired(Exception):
    pass

class PlayerNotRegisteredError(Exception):
    pass

class TooManyPlayersError(Exception):
    pass

class NotEnoughPlayersError(Exception):
    pass

class PlayerAlreadyPairedError(Exception):
    pass

class PlayerNotPairedError(Exception):
    pass

class GameRunningError(Exception):
    pass

class MasterRemoteAlreadyPairedError(Exception):
    pass

class GameAlreadyPausedError(Exception):
    pass

class GameNotPausedError(Exception):
    pass
