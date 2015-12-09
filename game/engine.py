from score import ScoreHandler, PlayerScore
from nrf24 import NRF24Handler
from remote import RemoteDecoder, RemoteCommands, RemotePairFailureType, RemotePairHandler
import logging
from game_except import *
from timer import TimerHandler, TimerAnnouncement
from game_persist import GamePersistance, PlayerPersistData
from soundfx import GameSFXHandler
from game.remotemapper import RemoteMapping, RemoteMappingLoadFailed
from game.constants import GameTurnActions, MasterRemoteActions
from game.sfxmapper import SFXMapping, SFXMappingLoadFailed, SFXUnknownEvent, SFXMappableEvents

#remote pairing timeout in seconds
GAME_PAIRING_TIMEOUT = 30

class MasterRemote(object):

    def __init__(self):
        self.remote_id = None

class ChainballGame(object):

    def __init__(self, virtual_hw=False):

        self.logger = logging.getLogger('sboard.game')

        self.s_handler = ScoreHandler('/dev/ttyAMA0', virt_hw=virtual_hw)
        self.rf_handler = NRF24Handler(fake_hw=virtual_hw)

        #load remote mapping configuration file
        try:
            self.remote_mapping = RemoteMapping(self.logger)
            self.remote_mapping.load_config('conf/remotemap.json')
        except RemoteMappingLoadFailed:
            self.logger.error('Failed to load remote button mapping')
            exit(1)

        #load SFX mapping configuration file
        try:
            self.sfx_mapping = SFXMapping()
            self.sfx_mapping.load_config('conf/game.json')
        except SFXMappingLoadFailed:
            self.logger.error('Failed to load SFX mapping')

        #remote pair handler (non-threaded)
        self.pair_handler = RemotePairHandler(fail_cb=self.pair_fail,
                                              success_cb=self.pair_end)
        
        #timer handler
        self.timer_handler = TimerHandler(self.game_timeout, self)

        #create player dictionary
        self.players = dict([(x, PlayerScore(self.s_handler, x, autoadv_cb=self.game_pass_turn)) for x in range(4)])
        self.player_count = 0

        #game persistance
        #self.g_persist = GamePersistance('games')

        #set flags
        self.ongoing = False
        self.active_player = None
        self.game_uuid = None
        self.paused = False
        self.error = False

        #start rf handler
        self.rf_handler.start()

        #start score handler
        self.s_handler.start()

        #master remote
        self.m_remote = MasterRemote()

        #sound effects
        self.sfx_handler = GameSFXHandler()

    def post_init(self):

        self.timer_handler.announcement(TimerAnnouncement("CHAIN", "BALL", self.init_announcement_end), 10)

    def init_announcement_end(self):
        self.timer_handler.setup(20)

    def unpair_remote(self, player):

        if player not in self.players:
            raise KeyError('Invalid Player')

        if self.players[player].registered == False:
            raise PlayerNotRegisteredError('Player not registered')

        if self.players[player].remote_id == None:
            raise PlayerNotPairedError('Player not paired to a remote')

        self.logger.info('Unpairing remote {} for player {}'.format(self.players[player].remote_id,
                                                                    player))

        self.pair_handler.stop_tracking(self.players[player].remote_id)
        self.players[player].remote_id = None

    def pair_master(self):

        if self.m_remote.remote_id != None:
            raise MasterRemoteAlreadyPairedError('Already paired to {}'.format(self.m_remote.remote_id))
        #pair
        self.pair_handler.start_pair("master")

    def unpair_master(self):

        self.pair_handler.stop_tracking(self.m_remote.remote_id)
        self.m_remote.remote_id = None

    def pair_remote(self, player):

        if player not in self.players:
            raise KeyError('Invalid player')

        if self.players[player].registered == False:
            raise PlayerNotRegisteredError('Player not registered')

        if self.players[player].remote_id:
            raise PlayerAlreadyPairedError('Already paired to {}'.format(self.players[player].remote_id))

        #start pairing
        self.pair_handler.start_pair(player)

    def pair_end(self, player, remote_id):

        if player == "master":
            self.m_remote.remote_id = remote_id
            self.logger.info('Paired remote {} as the master remote'.format(remote_id))
            return

        self.players[player].remote_id = remote_id
        self.logger.info('Paired player {} to remote {}'.format(player,
                                                                self.players[player].remote_id))

    def pair_fail(self, player, reason=None):
        if reason == RemotePairFailureType.TIMEOUT:
            self.logger.info('Pairing for player {} failed due to a timeout'.format(player))
        elif reason == RemotePairFailureType.ALREADY_PAIRED:
            self.logger.info('Pairing for player {} failed: remote is already paired'.format(player))
        else:
            self.logger.info('Pairing for player {} failed due to an unknown reason'.format(player))

    def pair_running(self):
        if self.pair_handler.is_running():
            return ['PAIR', None]
        elif self.pair_handler.has_failed() != None:
            return ['FAIL', self.pair_handler.has_failed()]

        return ['IDLE', None]

    def shutdown(self):
        self.s_handler.stop()
        self.rf_handler.stop()
        self.s_handler.join()
        self.rf_handler.join()

    def game_can_start(self):
        #check that at least 2 players are registered
        if self.player_count < 2:
            return False

        #check that all players have paired remotes
        for player in self.players:
            if self.players[player].registered == False:
                continue

            if self.players[player].remote_id == None:
                return False

        return True

    def do_announcement(self, announcement, duration, dont_handle=False):

        if dont_handle == False:
            #save callback
            original_cb = announcement.cb

            #insert our callback
            announcement.cb = self.default_announcement_end
            announcement.cb_args = original_cb

        self.timer_handler.announcement(announcement, duration)

    def do_player_announcement(self, player_number, announcement, duration, dont_handle=False):

        if dont_handle == False:
            #save callback
            original_cb = announcement.cb

            #insert our callback
            announcement.cb = self.default_announcement_end
            announcement.cb_args = original_cb

        self.timer_handler.player_announcement(announcement, duration, player_number)

    def default_announcement_end(self, original_cb=None):

        if not self.ongoing:
            self.timer_handler.setup(20)

        #original callback
        if original_cb:
            original_cb()

    def register_players(self, player_texts):
        if self.ongoing:
            raise GameRunningError('Cant register players while running')

        if len(player_texts) > 4 - self.player_count:
            raise TooManyPlayersError('Limited to 4 players')

        for player in player_texts:
            if player > 3 or player < 0:
                #ignore this for now
                self.logger.debug('Invalid player, ignoring')
                continue

            if player in self.players:
                #ignore
                if self.players[player].registered:
                    self.logger.debug('Player {} is already registered, ignoring'.format(player))
                    continue

            self.s_handler.register_player(player, player_texts[player].panel_txt)
            self.players[player].web_text = player_texts[player].web_txt
            self.players[player].panel_text = player_texts[player].panel_txt
            self.players[player].registered = True
            self.player_count += 1

            self.logger.debug('Registered player {}'.format(player))

    def next_player_num(self):

        for player in self.players:
            if self.players[player].registered == False:
                return player

        raise TooManyPlayersError


    def unregister_players(self, players):

        if self.ongoing:
            raise GameRunningError('cant unregister players while running')

        for player in players:
            if player not in self.players:
                #ignore
                continue

            if self.players[player].registered == False:
                #ignore
                continue

            self.s_handler.unregister_player(player)
            self.players[player].web_text = None
            self.players[player].panel_text = None
            self.players[player].registered = False
            self.pair_handler.stop_tracking(self.players[player].remote_id)
            self.players[player].remote_id = None
            self.player_count -= 1

    def game_begin(self):
        self.logger.info('Starting game...')
        if self.ongoing:
            raise GameAlreadyStarterError('Game is running')

        if self.player_count < 2:
            raise NotEnoughPlayersError('Game needs at least 2 players')

        #check if remotes are paired
        for player in self.players:
            if self.players[player].remote_id == None and self.players[player].registered:
                raise PlayerRemoteNotPaired('Player {} has no remote paired'.format(player))

        #clear scores and prepare data
        player_persist = {}
        for player in self.players:
            if self.players[player].registered:
                self.game_set_score(player, 0)
                #player_persist[player] = PlayerPersistData(self.players[player].web_text)

        #create persistance data
        #self.game_uuid = self.g_persist.new_record(player_persist)

        #flag game start
        self.ongoing = True
        self.paused = False
        self.game_set_active_player(0)

        self.timer_handler.start(20)

        self.timer_handler.announcement(TimerAnnouncement("Game", "START"), 2)
        self.logger.info('Game started')

    def find_high_score(self):
        winner_score = -10
        winner_player = 0
        for player in self.players:
            if self.players[player].current_score > winner_score:
                winner_player = player
                winner_score = self.players[player].current_score

        return winner_player

    def game_timeout(self):

        self.logger.info('Game has run out of time')
        #winner_player = self.find_high_score()

        #self.s_handler.set_turn(winner_player)
        #self.announce_end(winner_player)
        self.game_end()

    def game_pause(self):

        if not self.ongoing:
            raise GameNotStartedError('game is not running')

        if self.paused:
            raise GameAlreadyPausedError('game is already paused')

        self.logger.info('Game PAUSED')
        self.paused = True
        self.timer_handler.pause()

    def game_unpause(self):

        if not self.ongoing:
            raise GameNotStartedError('game is not running')

        if not self.paused:
            raise GameNotPausedError('game is not paused')

        self.logger.info('Game UNPAUSED')
        self.paused = False
        self.timer_handler.unpause()

    def game_end(self):
        self.logger.info('Stopping game...')
        if not self.ongoing:
            raise GameNotStartedError('Game is not running')

        winner_player = self.find_high_score()

        self.s_handler.set_turn(winner_player)
        self.announce_end(winner_player)

        #play sfx
        try:
            game_end_sfx = self.sfx_mapping.get_sfx(SFXMappableEvents.GAME_END)
            self.sfx_handler.play_fx(game_end_sfx)
        except SFXUnknownEvent:
            pass

        self.timer_handler.stop()
        self.ongoing = False

        #self.g_persist.end_game()
        self.game_uuid = None

        self.logger.info('Game stopped')

    def game_set_active_player(self, player):

        if not self.ongoing:
            raise GameNotStartedError('Game is not running')

        #see if player is registered
        if self.players[player].registered == False:
            raise PlayerNotRegisteredError('Player is not taking part in game')

        for p in self.players:
            self.players[p].score_diff = 0
            if p == player:
                self.players[p].is_turn = True
                self.active_player = p
            else:
                self.players[p].is_turn = False

    def announce_player_deltas(self, player):

        if player > self.player_count - 1:
            return

        if player not in self.players:
            return

        #don't announce players with zero score delta
        for p in range(player, self.player_count):
            if self.players[p].score_diff == 0 or self.players[p].current_score == -10:
                continue
            else:
                self.timer_handler.announcement(TimerAnnouncement(self.players[p].panel_text,
                                                                  '{:+1d}'.format(self.players[p].score_diff)),
                                                2)
                self.timer_handler.player_announcement(TimerAnnouncement('',
                                                                         '{:+1d} -> {:+1d}'.format(self.players[p].score_diff,
                                                                                                   self.players[p].current_score)),
                                                       5,
                                                       p)

    def game_pass_turn(self):

        if not self.ongoing:
            raise GameNotStartedError('Game is not running')

        #reset all serves immediately
        self.logger.debug('Resetting serve states')
        for player in self.players:
            self.players[player].reset_serve()

        #announce score deltas
        self.announce_player_deltas(0)
        #self.timer_handler.announcement(TimerAnnouncement(self.players[self.active_player].panel_text,
        #                                                  '{:+1d}'.format(self.players[self.active_player].score_diff)), 2)


        for p in range(self.active_player + 1, self.player_count):
            if self.players[p].current_score != -10:
                self.game_set_active_player(p)
                return

        #reaching here, begin at player 0 score
        for p in range(0, self.active_player):
            if self.players[p].current_score != -10:
                self.game_set_active_player(p)
                return

        #if self.active_player < self.player_count - 1:
        #    self.game_set_active_player(self.active_player + 1)
        #else:
        #    self.game_set_active_player(0)

    def game_player_out(self, player):
        #play sound here, announce
        self.logger.debug('Player {} is out of the game!'.format(player))

        self.timer_handler.announcement(TimerAnnouncement(self.players[player].panel_text, "COWOUT"), 4)

        try:
            cowout_sfx = self.sfx_mapping.get_sfx(SFXMappableEvents.COW_OUT)
            self.sfx_handler.play_fx(cowout_sfx)
        except SFXUnknownEvent:
            self.logger.warning('SFX play error')

    def game_decrement_score(self, player):

        if player == None:
            return

        if not self.players[player].registered:
            return

        if self.paused or not self.ongoing:
            return

        if self.players[player].current_score > -10 and self.players[player].score_diff > -2:
            self.players[player].current_score -= 1
            self.players[player].score_diff -= 1

            #check here if we have reached -10
            if self.players[player].current_score == -10:
                #player is out of the game
                self.game_player_out(player)
                return

        #TODO IF A PLAYER HITS -10 HES OUT OF THE GAME, PLAY SOUND - OK
        #TODO AT GAME END, PLAY SOUND - OK
        #TODO ADVANCE SERVE AUTOMATICALLY - OK

    def game_increment_score(self, player):

        if player == None:
            return

        if not self.players[player].registered:
            return

        if self.paused or not self.ongoing:
                return

        if self.players[player].current_score < 5 and self.players[player].score_diff < 2:
            self.players[player].current_score += 1
            self.players[player].score_diff += 1

    def game_set_score(self, player, score):
        self.players[player].current_score = score

    def _game_decode_remote(self, message):

        #handle pairing
        if self.pair_handler.remote_event(message):
            return

        #master
        if message.remote_id == self.m_remote.remote_id:
            #master remote actions
            if message.command == RemoteCommands.BTN_PRESS:
                if self.remote_mapping.master_mapping[message.cmd_data] == MasterRemoteActions.PAUSE_UNPAUSE_CLOCK:
                    if not self.ongoing:
                        if self.game_can_start():
                            self.game_begin()
                        return

                    if self.paused:
                        self.game_unpause()
                    else:
                        self.game_pause()
            return

        if not self.ongoing:
            return

        #if message.remote_id != self.players[self.active_player].remote_id:
        #    self.logger.debug('Ignored message from other player remote')
        #    return

        if self.paused:
            return

        commanding_player = self.find_player_by_remote(message.remote_id)

        if message.command == RemoteCommands.BTN_PRESS:
            if self.remote_mapping.player_mapping[message.cmd_data] == GameTurnActions.DECREASE_SCORE:
                self.game_decrement_score(commanding_player)
            elif self.remote_mapping.player_mapping[message.cmd_data] == GameTurnActions.INCREASE_SCORE:
                self.game_increment_score(commanding_player)
            elif self.remote_mapping.player_mapping[message.cmd_data] == GameTurnActions.PASS_TURN:
                if message.remote_id != self.players[self.active_player].remote_id:
                    self.logger.debug('Only the active player can force the serve')
                    return
                self.game_pass_turn()

    def find_player_by_remote(self, remote_id):
        for player in self.players:
            if self.players[player].remote_id == remote_id:
                return player

    def count_players_out(self):

        players_out = 0
        for player in self.players:
            if self.players[player].current_score == -10:
                players_out += 1

        return players_out

    def game_swap_players(self, players):
        return

        self.logger.debug('swapping players {}<->{}'.format(*players))

        #this is very rudimentary, swap players by changing associated values
        player, other_player = self.players[players[0]], self.players[players[1]]

        #save temporary
        temp_player = PlayerScore()
        temp_player.copy(self.players[players[0]])
        #temp_player.handler = None
        #temp_player.pid = player.pid
        #temp_player.current_score = player.current_score
        #temp_player.is_turn = player.is_turn
        #temp_player.web_text = player.web_text
        #temp_player.panel_text = player.panel_text
        #temp_player.remote_id = player.remote_id

        #swap one
        #player.pid = None
        #player.pid = other_player.pid
        #player.current_score = None
        #player.current_score = other_player.current_score
        #player.is_turn = None
        #player.is_turn = other_player.is_turn
        #player.web_text = other_player.web_text[:]
        #player.panel_text = other_player.panel_text[:]
        #player.remote_id = None
        #player.remote_id = other_player.remote_id
        self.players[players[0]].copy(self.players[players[1]])
        self.players[players[1]].copy(temp_player)
        #swap the other
        #other_player.pid = temp_player.pid
        #other_player.current_score = temp_player.current_score
        #other_player.is_turn = temp_player.is_turn
        #other_player.web_text = temp_player.web_text[:]
        #other_player.panel_text = temp_player.panel_text[:]
        #other_player.remote_id = temp_player.remote_id

    def announce_end(self, winner):
        self.do_announcement(TimerAnnouncement(self.players[winner].panel_text,
                                               "WINS!",
                                               self.force_show_clock), 10, True)

    def force_show_clock(self):
        self.timer_handler.refresh_matrix()

    def game_loop(self):

        #handle serves
        if self.ongoing:
            for player in self.players:
                self.players[player].handle_serve()

        #handle SFX
        self.sfx_handler.handle()

        #handle pairing
        self.pair_handler.handle()

        #handle timer
        self.timer_handler.handle()

        #check for a winner
        if self.ongoing:
            if self.count_players_out() >= self.player_count - 1:
                self.logger.info('Only one player remais! Ending')
                self.game_timeout()
                return

            for player in self.players:
                if self.players[player].current_score == 5:
                    self.logger.info('Player {} has won the game'.format(player))
                    self.announce_end(player)
                    self.game_end()
                    return

        #check for remote activity
        if self.rf_handler.message_pending():
            message = self.rf_handler.receive_message()
            #process message
            try:
                decoded = RemoteDecoder(message.payload)
            except IOError:
                #invalid, ignore
                return

            self.logger.debug('Received: {}'.format(decoded))
            self._game_decode_remote(decoded)

        #throttle game loop
        #time.sleep(0.01)