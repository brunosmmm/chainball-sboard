import json
import datetime
import logging
from os import listdir
from os.path import isfile, join

class CannotModifyScoresError(Exception):
    pass

class PlayerPersistData(object):
    def __init__(self, display_name, player_name=None):
        self.display_name = display_name
        self.player_name = player_name
        self.score = 0

    def update_score(self, score):
        self.score = score

    def get_data(self):
        data = {}

        data['display_name'] = self.display_name
        data['full_name'] = self.player_name
        data['score'] = self.score

        return data

class GamePersistStates(object):
    RUNNING = 0
    FINISHED = 1
    PAUSED = 2

    NAMES = {RUNNING: 'RUNNING',
             FINISHED: 'FINISHED',
             PAUSED: 'PAUSED'}

class GameEventTypes(object):
    SCORE_CHANGE = 'SCORE_CHANGE'
    COWOUT = 'COWOUT'
    GAME_END = 'GAME_END'
    GAME_PAUSE = 'GAME_PAUSE'
    GAME_UNPAUSE = 'GAME_UNPAUSE'
    FORCE_SERVE = 'FORCE_SERVE'
    DEADBALL = 'DEADBALL'
    MUDSKIPPER = 'MUDSKIPPER'
    RATMEAT = 'RATMEAT'
    SAILORMOON = 'SAILORMOON'
    CHAINBALL = 'CHAINBALL'
    JAILBREAK = 'JAILBREAK'
    DOUBLEFAULT = 'DOUBLEFAULT'
    SLOWPOKE = 'SLOWPOKE'

class GamePersistData(object):

    def __init__(self, players, handler):
        #initialize scores
        self.player_data = players
        self.game_state = GamePersistStates.RUNNING
        self.start_time = datetime.datetime.now()
        self.data_change_handler = handler
        self.events = []

        #if self.data_change_handler:
        #    self.data_change_handler()

    def update_score(self, player, score, forced_update=False):

        if player not in self.player_data:
            raise KeyError('Invalid Player')

            if self.game_state == GamePersistStates.FINISHED:
                raise CannotModifyScoresError('Game has finished')

        self.player_data[player].update_score(score)

        if forced_update is False:
            self.log_event(GameEventTypes.SCORE_CHANGE,
                           {'player': player,
                            'new_score': score})
        else:
            if self.data_change_handler:
                self.data_change_handler()

    def end_game(self, reason, winner):

        self.game_state = GamePersistStates.FINISHED
        self.log_event(GameEventTypes.GAME_END, {'reason': reason,
                                                 'winner': winner})
        #if self.data_change_handler:
        #    self.data_change_handler()

    def pause_unpause(self):
        if self.game_state == GamePersistStates.RUNNING:
            self.game_state = GamePersistStates.PAUSED
            self.log_event(GameEventTypes.GAME_PAUSE, None)
        elif self.game_state == GamePersistStates.PAUSED:
            self.game_state = GamePersistStates.RUNNING
            self.log_event(GameEventTypes.GAME_UNPAUSE, None)

        #if self.data_change_handler:
        #    self.data_change_handler()

    def log_event(self, evt_type, evt_desc, save=True):
        self.events.append({'evt_type': evt_type,
                            'evt_desc': evt_desc,
                            'evt_time': str(datetime.datetime.now())})

        if save is True and self.data_change_handler:
            self.data_change_handler()

    def to_JSON(self):

        json_dict = {}
        json_dict['start_time'] = str(self.start_time)
        json_dict['game_state'] = GamePersistStates.NAMES[self.game_state]
        player_dict = {}

        for player_num, player_data in self.player_data.iteritems():
            player_dict[str(player_num)] = player_data.get_data()

        json_dict['events'] = self.events

        json_dict['player_data'] = player_dict
        return json_dict

class GamePersistance(object):

    def __init__(self, folder):

        self.logger = logging.getLogger('sboard.gpersist')
        self.path = folder
        self.game_history = {}
        self.current_game = None
        self.current_game_series = 0

        self.load_history()

    def load_history(self):

        # load current game number
        try:
            with open('data/persist/game.json', 'r') as f:
                persist_data = json.load(f)
                self.current_game_series = persist_data['current_series']
        except:
            self.logger.error('Could not load overall game persistance data')

        for f in listdir('./'+self.path):
            if isfile(join('./'+self.path, f)):
                file_uuid = f.split('.')[0]

                try:
                    with open(join(self.path, f), 'r') as g:
                        game_data = json.load(g)
                except:
                    #raise
                    self.logger.warning('Could not load game persistance for game {}'.format(f))
                    continue

                self.game_history[file_uuid] = game_data

    def new_record(self, players):
        game_uuid = '{s:06d}'.format(s=self.current_game_series)
        self.current_game_series += 1
        self.current_game = game_uuid
        self.game_history[game_uuid] = GamePersistData(players, self.save_current_data)
        self.save_current_data()

        return game_uuid

    def log_event(self, evt_type, evt_desc):
        try:
            self.game_history[self.current_game].log_event(evt_type,
                                                           evt_desc)
        except:
            pass

    def end_game(self, reason, winner):
        try:
            self.game_history[self.current_game].end_game(reason, winner)
        except:
            pass
        self.current_game = None

    def pause_unpause_game(self):
        try:
            self.game_history[self.current_game].pause_unpause()
        except:
            pass

    def update_current_score(self, player, score, forced_update):
        try:
            self.game_history[self.current_game].update_score(player, score, forced_update)
        except:
            pass

    def save_current_data(self):

        # save game series number
        try:
            with open('data/persist/game.json', 'w') as f:
                json.dump({'current_series': self.current_game_series}, f)
        except:
            self.logger.error('Could not save overall game persistance state')

        file_name = join(self.path, self.current_game + '.json')

        try:
            with open(file_name, 'w') as f:
                #f.write(self.game_history[self.current_game].to_JSON())
                json.dump(self.game_history[self.current_game].to_JSON(), f)
        except:
            self.logger.error('Could not save game persistance data')
            #raise
