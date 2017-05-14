"""Game Persistance."""

import json
import datetime
import logging
from os import listdir
from os.path import isfile, join


class CannotModifyScoresError(Exception):
    """Unable to modify scores."""

    pass


class PlayerPersistData(object):
    """Persistent data for a player."""

    def __init__(self, display_name, player_name=None):
        """Initialize.

        Args
        ----
        display_name: str
           Name shown on display
        player_name: str
           Full name, displayed on web interface
        """
        self.display_name = display_name
        self.player_name = player_name
        self.score = 0

    def update_score(self, score):
        """Update player score."""
        self.score = score

    def get_data(self):
        """Return current data for player."""
        data = {}

        data['display_name'] = self.display_name
        data['full_name'] = self.player_name
        data['score'] = self.score

        return data


class GamePersistStates(object):
    """Game States."""

    RUNNING = 0
    FINISHED = 1
    PAUSED = 2

    NAMES = {RUNNING: 'RUNNING',
             FINISHED: 'FINISHED',
             PAUSED: 'PAUSED'}


class GameEventTypes(object):
    """Events that occur during a game."""

    SCORE_CHANGE = 'SCORE_CHANGE'
    SCORE_FORCED = 'SCORE_FORCED'
    COWOUT = 'COWOUT'
    GAME_START = 'GAME_START'
    GAME_END = 'GAME_END'
    GAME_PAUSE = 'GAME_PAUSE'
    GAME_UNPAUSE = 'GAME_UNPAUSE'
    FORCE_SERVE = 'FORCE_SERVE'
    DEADBALL = 'DEADBALL'
    MUDSKIPPER = 'MUDSKIPPER'
    BALL_HIT = 'BALL_HIT'
    SAILORMOON = 'SAILORMOON'
    CHAINBALL = 'CHAINBALL'
    JAILBREAK = 'JAILBREAK'
    FAULT = 'FAULT'
    DOUBLEFAULT = 'DOUBLEFAULT'
    SLOWPOKE = 'SLOWPOKE'
    SERVE_ADVANCE = 'SERVE_ADVANCE'


class GamePersistData(object):
    """Game persistance data structures."""

    def __init__(self, players, handler, current_series):
        """Initialize.

        Args
        ----
        players: dict
           Dictionary of player data indexed by player number
        handler: unknown
           Not sure
        current_series: int
           Current game identifier (persistent value always increasing)
        """
        self.player_data = players
        self.game_state = GamePersistStates.RUNNING
        self.start_time = datetime.datetime.now()
        self.data_change_handler = handler
        self.events = []
        self.internal_game_id = current_series
        self.user_game_id = None

        # if self.data_change_handler:
        #     self.data_change_handler()

    def assign_user_id(self, user_id):
        """Assign an identifier to current game.

        Args
        ----
        user_id: str
           An identifier for this particular game
        """
        self.user_game_id = user_id

        if self.data_change_handler is not None:
            self.data_change_handler()

    def update_score(self, player, score, forced_update=False, game_time=None):
        """Update player score record.

        Args
        ----
        player: int
            Player number
        score: int
            New score
        forced_update: bool
            Is this a forced update or a normal update; i.e. from scoring evt
        game_time: int
            Current game time in seconds
        """
        if player not in self.player_data:
            raise KeyError('Invalid Player')

        if self.game_state == GamePersistStates.FINISHED:
            raise CannotModifyScoresError('Game has finished')

        old_score = self.player_data[player].score
        self.player_data[player].update_score(score)

        if forced_update is False:
            self.log_event(GameEventTypes.SCORE_CHANGE,
                           {'player': player,
                            'old_score': old_score,
                            'new_score': score,
                            'gtime': game_time})
        else:
            if self.data_change_handler is not None:
                self.data_change_handler()

    def force_score(self, player, score, game_time=None):
        """Force score for a player.

        Args
        ----
        player: int
           Player number
        score: int
           New score
        game_time: int
           Current game time in seconds
        """
        if player not in self.player_data:
            raise KeyError('Invalid Player')

        if self.game_state == GamePersistStates.FINISHED:
            raise CannotModifyScoresError('Game has finished')

        old_score = self.player_data[player].score
        self.player_data[player].update_score(score)

        self.log_event(GameEventTypes.SCORE_FORCED,
                       {'player': player,
                        'old_score': old_score,
                        'new_score': score,
                        'gtime': game_time})

    def start_game(self, remaining_time):
        """Log start of game.

        Args
        ----
        remaining_time: int
           Game duration
        """
        # doesnt change the current status for now, but i think it should
        self.log_event(GameEventTypes.GAME_START, {'rtime': remaining_time,
                                                   'gtime': 0})

    def end_game(self, reason, winner, running_time, remaining_time):
        """Log end of game.

        Args
        ----
        reason: uknown
            Reason for end of game
        winner: int
            Winner player number
        running_time: int
            Current game time in seconds
        remaining_time: int
            Remaining time at end, in seconds
        """
        self.game_state = GamePersistStates.FINISHED
        self.log_event(GameEventTypes.GAME_END, {'reason': reason,
                                                 'winner': winner,
                                                 'gtime': running_time,
                                                 'rtime': remaining_time})
        # if self.data_change_handler:
        #     self.data_change_handler()

    def pause_unpause(self):
        """Pause or unpause game."""
        if self.game_state == GamePersistStates.RUNNING:
            self.game_state = GamePersistStates.PAUSED
            self.log_event(GameEventTypes.GAME_PAUSE, None)
        elif self.game_state == GamePersistStates.PAUSED:
            self.game_state = GamePersistStates.RUNNING
            self.log_event(GameEventTypes.GAME_UNPAUSE, None)

        # if self.data_change_handler:
        #     self.data_change_handler()

    def log_event(self, evt_type, evt_desc, save=True):
        """Log an event.

        Args
        ----
        evt_type: GameEventTypes
           Event type
        evt_desc: str
           A description for the event
        save: bool
           Whether to save to disk immediately
        """
        self.events.append({'evt_type': evt_type,
                            'evt_desc': evt_desc,
                            'evt_time': str(datetime.datetime.now())})

        if save is True and self.data_change_handler is not None:
            self.data_change_handler()

    def to_JSON(self):
        """Dump a JSON representation of the current game."""
        json_dict = {}
        json_dict['start_time'] = str(self.start_time)
        json_dict['game_state'] = GamePersistStates.NAMES[self.game_state]
        player_dict = {}

        for player_num, player_data in self.player_data.iteritems():
            player_dict[str(player_num)] = player_data.get_data()

        json_dict['events'] = self.events

        json_dict['player_data'] = player_dict

        game_data = {}
        game_data['internal_id'] = self.internal_game_id
        game_data['user_id'] = self.user_game_id

        json_dict['game_data'] = game_data

        return json_dict


class GamePersistance(object):
    """Game persistance data wrapper class."""

    def __init__(self, folder):
        """Initialize.

        Args
        ----
        folder: str
           Path where game persistance files are stored
        """
        self.logger = logging.getLogger('sboard.gpersist')
        self.path = folder
        self.game_history = {}
        self.current_game = None
        self.current_game_series = 0
        self._test_mode = False

        self.load_history()

    def load_history(self):
        """Load all games saved previously."""
        # load current game number
        try:
            f = open('data/persist/game.json', 'r')
            persist_data = json.load(f)
            self.current_game_series = persist_data['current_series']
        except:
            self.logger.error('Could not load overall game persistance data')
            return

        try:
            flist = listdir('./'+self.path)
            repr(flist)
        except:
            self.logger.error('Could not load individual game persistances')
            return

        for f in listdir('./'+self.path):
            if isfile(join('./'+self.path, f)):
                file_uuid = f.split('.')[0]

                try:
                    with open(join(self.path, f), 'r') as g:
                        game_data = json.load(g)
                except:
                    # raise
                    self.logger.warning('Could not load game '
                                        'persistance for game {}'.format(f))
                    continue

                self.game_history[file_uuid] = game_data

    def new_record(self, players):
        """Create new game record.

        Args
        ----
        players: dict
            Player dictionary
        """
        game_uuid = '{s:06d}'.format(s=self.current_game_series)
        self.current_game_series += 1
        self.current_game = game_uuid
        self.game_history[game_uuid] =\
            GamePersistData(players,
                            self.save_current_data,
                            self.current_game_series)
        self.save_current_data()

        return game_uuid

    def log_event(self, evt_type, evt_desc):
        """Log an event.

        Args
        ----
        evt_type: GameEventTypes
           Event type
        evt_desc: str
           Event description
        """
        try:
            self.game_history[self.current_game].log_event(evt_type,
                                                           evt_desc)
        except:
            pass

    def start_game(self, remaining_time):
        """Log start of game.

        Args
        ----
        remaining_time: int
           Game clock duration
        """
        try:
            self.game_history[self.current_game].start_game(remaining_time)
        except:
            pass

    def end_game(self, reason, winner, running_time, remaining_time):
        """Log end of a game.

        Args
        ----
        reason: unknown
           unknown
        winner: int
           Winner player number
        running_time: int
           Current game time in seconds
        remaining_time: int
           Remaining time in seconds
        """
        try:
            self.game_history[self.current_game].end_game(reason,
                                                          winner,
                                                          running_time,
                                                          remaining_time)
        except:
            pass
        self.current_game = None

    def pause_unpause_game(self):
        """Pause or unpause game."""
        try:
            self.game_history[self.current_game].pause_unpause()
        except:
            pass

    def update_current_score(self, player, score, forced_update, game_time):
        """Update scores.

        Args
        ----
        player: int
           Player number
        score: int
           Current score
        force_update: bool
           Forced update or not
        game_time: int
           Current game time in seconds
        """
        try:
            self.game_history[self.current_game].update_score(player,
                                                              score,
                                                              forced_update,
                                                              game_time)
        except:
            self.logger.error('could not update score: '
                              'player {}, score: {}, '
                              'forced: {}'.format(player,
                                                  score,
                                                  forced_update))

    def force_current_score(self, player, score, game_time):
        """Force a score value.

        Args
        ----
        player: int
            Player number
        score: int
            New score
        game_time: int
            Current game time
        """
        try:
            self.game_history[self.current_game].force_score(player,
                                                             score,
                                                             game_time)
        except:
            pass

    def save_current_data(self):
        """Save data immediately."""
        # save game series number
        try:
            if self._test_mode is True:
                raise
            with open('data/persist/game.json', 'w') as f:
                json.dump({'current_series': self.current_game_series},
                          f,
                          indent=4)
        except:
            self.logger.error('Could not save overall game persistance state')

        file_name = join(self.path, self.current_game + '.json')

        try:
            if self._test_mode is True:
                raise
            with open(file_name, 'w') as f:
                json.dump(self.game_history[self.current_game].to_JSON(),
                          f,
                          indent=4)
        except:
            self.logger.error('Could not save game persistance data')

    def assign_user_id(self, user_id):
        """Assign user id to current game.

        Args
        ----
        user_id: str
           An user defined identifier
        """
        try:
            self.game_history[self.current_game].assign_user_id(user_id)
        except:
            self.logger.error('Could not assign user id to game')

    def get_current_user_id(self):
        """Get user identifier for current game."""
        try:
            return self.game_history[self.current_game].user_game_id
        except:
            return None
