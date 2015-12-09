import json
import datetime
from uuid import uuid1, UUID
import logging
from os import listdir
from os.path import isfile, join

class CannotModifyScoresError(Exception):
    pass

class PlayerPersistData(object):
    def __init__(self, display_name):
        self.display_name = display_name
        self.score = 0

    def update_score(self, score):
        self.score = score

class GamePersistStates(object):
    RUNNING = 0
    FINISHED = 1
    PAUSED = 2

class GamePersistData(object):

    def __init__(self, players, handler):
        #initialize scores
        self.player_data = players
        self.game_state = GamePersistStates.RUNNING
        self.start_time = datetime.datetime.now()
        self.data_change_handler = handler

        #if self.data_change_handler:
        #    self.data_change_handler()

    def update_score(self, player, score):

        if player not in self.player_data:
            raise KeyError('Invalid Player')

            if self.game_state == GamePersistStates.FINISHED:
                raise CannotModifyScoresError('Game has finished')

        self.player_data[player].update_score(score)

        if self.data_change_handler:
            self.data_change_handler()

    def end_game(self):

        self.game_state = GamePersistStates.FINISHED

        if self.data_change_handler:
            self.data_change_handler()

    def to_JSON(self):

        json_dict = {}

        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

class GamePersistance(object):

    def __init__(self, folder):

        self.logger = logging.getLogger('sboard.gpersist')
        self.path = folder
        self.game_history = {}
        self.current_game = None

        self.load_history()

    def load_history(self):
        for f in listdir('./'+self.path):
            if isfile(join('./'+self.path, f)):
                file_uuid = f.split('.')[0]

                try:
                    with open(f, 'r') as g:
                        game_data = json.load(f)
                except:
                    self.logger.warning('Could not load game persistance for game {}'.format(f))
                    continue

                self.game_history[file_uuid] = game_data

    def new_record(self, players):
        game_uuid = str(uuid1())
        self.current_game = game_uuid
        self.game_history[game_uuid] = GamePersistData(players, self.save_current_data)
        self.save_current_data()

        return game_uuid

    def end_game(self):
        self.game_history[self.current_game].end_game()
        self.current_game = None

    def save_current_data(self):
        return

        file_name = self.current_game + '.json'

        try:
            with open(file_name, 'w') as f:
                f.write(self.game_history[self.current_game].to_JSON())
                #json.dump(self.game_history[self.current_game].__dict__, f)
        except:
            self.logger.error('Could not save game persistance data')
            raise
