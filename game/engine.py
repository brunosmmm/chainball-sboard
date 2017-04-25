from score.handler import ScoreHandler
from score.player import PlayerScore
from remote.nrf24 import NRF24Handler
from remote.decoder import RemoteDecoder
from remote.constants import RemoteCommands, RemotePairFailureType
from remote.pair import RemotePairHandler
import logging
from game.exceptions import *
from announce.timer import TimerHandler, TimerAnnouncement
from game.persist import GamePersistance, PlayerPersistData, GameEventTypes
from util.soundfx import GameSFXHandler
from game.remotemapper import RemoteMapping, RemoteMappingLoadFailed
from game.constants import GameTurnActions, MasterRemoteActions
from game.sfxmapper import SFXMapping, SFXMappingLoadFailed, SFXUnknownEvent, SFXMappableEvents
from game.config import ChainballGameConfiguration


class MasterRemote(object):

    def __init__(self):
        self.remote_id = None

class ChainballGame(object):

    def __init__(self, virtual_hw=False):

        self.logger = logging.getLogger('sboard.game')

        self.s_handler = ScoreHandler('/dev/ttyAMA0', virt_hw=virtual_hw)
        self.rf_handler = NRF24Handler(fake_hw=virtual_hw)

        #load remote mapping configuration file
        self.remote_mapping = RemoteMapping(self.logger)
        try:
            self.remote_mapping.load_config('conf/remotemap.json')
        except RemoteMappingLoadFailed:
            self.logger.error('Failed to load remote button mapping')
            exit(1)

        #load SFX mapping configuration file
        self.sfx_mapping = SFXMapping()
        try:
            self.sfx_mapping.load_config('conf/game.json')
        except SFXMappingLoadFailed:
            self.logger.error('Failed to load SFX mapping')

        #load other game configuration
        self.game_config = ChainballGameConfiguration()
        try:
            self.game_config.load_config('conf/game.json')
        except:
            self.logger.error('Failed to load game configuration')

        #remote pair handler (non-threaded)
        self.pair_handler = RemotePairHandler(fail_cb=self.pair_fail,
                                              success_cb=self.pair_end)
        
        #timer handler for RGB matrix
        self.timer_handler = TimerHandler(self.game_timeout, self)
        #timer handler for player panels
        self.ptimer_handler = TimerHandler(self.game_timeout, self, False)

        #create player dictionary
        self.players = dict([(x, PlayerScore(self.game_config.serve_timeout,
                                             self.s_handler,
                                             x,
                                             autoadv_cb=self.game_pass_turn)) for x in range(4)])
        self.player_count = 0

        #game persistance
        self.g_persist = GamePersistance('data/persist/games')

        #set flags
        self.ongoing = False
        self.active_player = None
        self.game_uuid = None
        self.paused = False
        self.error = False
        self.score_display_ended = True

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
        self.pair_handler.start_pair("master", self.game_config.pair_timeout)

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
        self.pair_handler.start_pair(player, self.game_config.pair_timeout)

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
        self.logger.debug('shutting down game engine')
        self.s_handler.stop()
        self.rf_handler.stop()
        self.s_handler.join()
        self.rf_handler.join()
        self.logger.debug('game enging shutdown complete')

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


    def _reorganize_players(self):

        for p_id, p_data in self.players.iteritems():
            if p_data.registered is False:

                # empty slot, move up other players if available
                for p_num in range(p_id+1, 4):
                    if self.players[p_num].registered:
                        # move up
                        p_data.web_text = self.players[p_num].web_text
                        p_data.panel_text = self.players[p_num].panel_text
                        p_data.remote_id = self.players[p_num].remote_id
                        p_data.registered = True

                        # register panel
                        self.s_handler.register_player(p_id, p_data.panel_text)

                        # unregister player that has been moved up
                        self.players[p_num].web_text = None
                        self.players[p_num].panel_text = None
                        self.players[p_num].registered = False
                        self.players[p_num].remote_id = None
                        self.s_handler.unregister_player(p_num)

                        # done
                        break

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

        self._reorganize_players()

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

        # reorder players
        self._reorganize_players()

        #clear scores and prepare data
        player_persist = {}
        for player in self.players:
            if self.players[player].registered:
                self.game_set_score(player, 0)
                player_persist[player] = PlayerPersistData(self.players[player].panel_text, self.players[player].web_text)

        #create persistance data
        self.game_uuid = self.g_persist.new_record(player_persist)

        #flag game start
        self.ongoing = True
        self.paused = False
        self.game_set_active_player(0)

        self.timer_handler.start(self.game_config.game_duration)
        self.ptimer_handler.start(self.game_config.game_duration)

        #confirm start
        self.g_persist.start_game(self.get_remaining_time())

        self.timer_handler.announcement(TimerAnnouncement("Game", "START"), 2)
        self.logger.info('Game started')

    def get_remaining_time(self):
        """Get remaining time in seconds"""
        if self.ongoing is False:
            return None

        minutes, seconds = self.timer_handler.get_remaining_time()

        return minutes*60 + seconds

    def get_running_time(self):
        """Get running time in seconds"""
        if self.ongoing is False:
            return None

        #duration in seconds
        duration = self.game_config.game_duration*60

        return duration - self.get_remaining_time()

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
        self.game_end(reason='TIMEOUT',
                      winner=self.find_high_score())

    def game_pause(self):

        if not self.ongoing:
            raise GameNotStartedError('game is not running')

        if self.paused:
            raise GameAlreadyPausedError('game is already paused')

        self.g_persist.pause_unpause_game()

        self.logger.info('Game PAUSED')
        self.paused = True
        self.timer_handler.pause()
        self.ptimer_handler.pause()

    def game_unpause(self):

        if not self.ongoing:
            raise GameNotStartedError('game is not running')

        if not self.paused:
            raise GameNotPausedError('game is not paused')

        # check if all remotes are paired
        for p_id, p_data in self.players.iteritems():
            if p_data.registered and p_data.remote_id is None:
                # registered but unpaired
                raise PlayerRemoteNotPaired('Player {} has no remote paired'.format(p_id))

        self.g_persist.pause_unpause_game()

        self.logger.info('Game UNPAUSED')
        self.paused = False
        self.timer_handler.unpause()
        self.ptimer_handler.unpause()

    def game_end(self, reason=None, winner=None):
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
        self.ptimer_handler.stop()

        self.g_persist.end_game(reason,
                                winner,
                                self.get_running_time(),
                                self.get_remaining_time())

        self.ongoing = False
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
                #self.timer_handler.player_announcement(TimerAnnouncement('',
                #                                                         '{:+1d} -> {:+1d}'.format(self.players[p].score_diff,
                #                                                                                   self.players[p].current_score)),
                #                                       5,
                #                                       p)

    def game_pass_turn(self, force_serve=False):

        if not self.ongoing:
            raise GameNotStartedError('Game is not running')

        #reset all serves immediately
        self.logger.debug('Resetting serve states')
        for player in self.players:
            self.players[player].reset_serve()

        #create event in persistance
        if force_serve is True:
            self.g_persist.log_event(GameEventTypes.FORCE_SERVE,
                                     {'player': int(self.active_player),
                                      'gtime': self.get_running_time()})

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

    def game_decrement_score(self, player, referee_event=False):

        if player == None:
            return

        if not self.players[player].registered:
            return

        if self.paused or not self.ongoing:
            return

        if self.players[player].current_score > -10 and self.players[player].score_diff > -2:
            self.players[player].current_score -= 1
            self.players[player].score_diff -= 1

            #update persistance data
            self.g_persist.update_current_score(player,
                                                self.players[player].current_score,
                                                forced_update=referee_event,
                                                game_time=self.get_running_time())

            #check here if we have reached -10
            if self.players[player].current_score == -10:
                #player is out of the game
                self.g_persist.log_event(GameEventTypes.COWOUT,
                                         {'player': player,
                                          'gtime': self.get_running_time()})
                #self.game_player_out(player)
                return

        #TODO IF A PLAYER HITS -10 HES OUT OF THE GAME, PLAY SOUND - OK
        #TODO AT GAME END, PLAY SOUND - OK
        #TODO ADVANCE SERVE AUTOMATICALLY - OK

    def game_increment_score(self, player, referee_event=False):

        if player == None:
            return

        if not self.players[player].registered:
            return

        if self.paused or not self.ongoing:
            return

        if self.players[player].current_score < 5 and self.players[player].score_diff < 2:
            self.players[player].current_score += 1
            self.players[player].score_diff += 1

            # update persistance data
            self.g_persist.update_current_score(player,
                                                self.players[player].current_score,
                                                forced_update=referee_event,
                                                game_time=self.get_running_time())

    def game_force_score(self, player, score):
        self.players[player].force_score(score)

        if self.ongoing is True:
            # update persistance data
            self.g_persist.force_current_score(player,
                                               score,
                                               game_time=self.get_running_time())

    def game_set_score(self, player, score):
        self.players[player].current_score = score

        if self.ongoing is True:
            # update persistance data
            self.g_persist.update_current_score(player,
                                                score,
                                                forced_update=False,
                                                game_time=self.get_running_time())

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
                self.game_pass_turn(force_serve=True)

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
        temp_player = PlayerScore(self.game_config.serve_timeout)
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

    def end_score_display(self):
        self.score_display_ended = True

    # scoring events
    def scoring_evt(self, player, evt_type):
        if self.ongoing is False:
            return

        if evt_type == 'deadball':
            self.g_persist.log_event(GameEventTypes.DEADBALL,
                                     {'player': int(player),
                                      'gtime': self.get_running_time()})
            self.game_pass_turn()
        elif evt_type == 'chainball':
            self.g_persist.log_event(GameEventTypes.CHAINBALL,
                                     {'player': int(player),
                                      'gtime': self.get_running_time()})
            self.game_increment_score(int(player), referee_event=True)
        elif evt_type == 'jailbreak':
            self.g_persist.log_event(GameEventTypes.JAILBREAK,
                                     {'player': int(player),
                                      'gtime': self.get_running_time()})
            self.game_increment_score(int(player), referee_event=True)
            self.game_increment_score(int(player), referee_event=True)
        elif evt_type == 'ratmeat':
            self.g_persist.log_event(GameEventTypes.RATMEAT,
                                     {'player': int(player),
                                      'gtime': self.get_running_time()})
            self.game_decrement_score(int(player), referee_event=True)
        elif evt_type == 'mudskipper':
            self.g_persist.log_event(GameEventTypes.MUDSKIPPER,
                                     {'player': int(player),
                                      'gtime': self.get_running_time()})
            self.game_decrement_score(int(player), referee_event=True)
        elif evt_type == 'sailormoon':
            self.g_persist.log_event(GameEventTypes.SAILORMOON,
                                     {'player': int(player),
                                      'gtime': self.get_running_time()})
            self.game_decrement_score(int(player), referee_event=True)
            self.game_decrement_score(int(player), referee_event=True)
        elif evt_type == 'doublefault':
            self.g_persist.log_event(GameEventTypes.DOUBLEFAULT,
                                     {'player': int(player),
                                      'gtime': self.get_running_time()})
            self.game_decrement_score(int(player), referee_event=True)
        elif evt_type == 'slowpoke':
            self.g_persist.log_event(GameEventTypes.SLOWPOKE,
                                     {'player': int(player),
                                      'gtime': self.get_running_time()})
            self.game_decrement_score(int(player), referee_event=True)

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

        #handle player panel timer
        self.ptimer_handler.handle()

        #check for a cowout
        if self.ongoing:
            for player in self.players:
                if self.players[player].current_score == -10 and self.players[player].is_cowout is False:
                    self.players[player].is_cowout = True
                    self.game_player_out(player)

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
                    self.game_end(reason='PLAYER_WON',
                                  winner=player)
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

        #make score announcements
        if self.score_display_ended and self.ongoing:
            self.score_display_ended = False
            for p in self.players:
                if p > self.player_count - 1:
                    continue
                if p == self.player_count - 1:
                    callback = self.end_score_display
                else:
                    callback = None
                self.ptimer_handler.player_announcement(TimerAnnouncement('',
                                                                         '{:+1d}'.format(self.players[p].current_score), callback),
                                                       5,
                                                       p)



        #throttle game loop
        #time.sleep(0.01)
