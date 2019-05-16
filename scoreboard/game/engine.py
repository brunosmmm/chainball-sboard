"""Game engine."""

import logging
import os

from scoreboard.announce.timer import TimerAnnouncement, TimerHandler
from scoreboard.game.config import ChainballGameConfiguration
from scoreboard.game.constants import GameTurnActions, MasterRemoteActions
from scoreboard.game.exceptions import (
    GameAlreadyPausedError,
    GameAlreadyStarterError,
    GameNotPausedError,
    GameNotStartedError,
    GameRunningError,
    MasterRemoteAlreadyPairedError,
    NotEnoughPlayersError,
    PlayerAlreadyPairedError,
    PlayerNotPairedError,
    PlayerNotRegisteredError,
    PlayerRemoteNotPaired,
    TooManyPlayersError,
)
from scoreboard.game.persist import (
    GameEventTypes,
    GamePersistance,
    PlayerPersistData,
)
from scoreboard.game.remotemapper import RemoteMapping, RemoteMappingLoadFailed
from scoreboard.game.sfxmapper import (
    SFXMappableEvents,
    SFXMapping,
    SFXMappingLoadFailed,
    SFXUnknownEvent,
)
from scoreboard.remote.constants import RemoteCommands, RemotePairFailureType
from scoreboard.remote.decoder import RemoteDecoder
from scoreboard.remote.nrf24 import NRF24Handler
from scoreboard.remote.pair import RemotePairHandler
from scoreboard.score.handler import ScoreHandler
from scoreboard.score.player import PlayerScore
from scoreboard.util.soundfx import GameSFXHandler
from scoreboard.util.configfiles import (
    CHAINBALL_CONFIGURATION,
    ChainBallConfigurationError,
)


class ChainballGameError(Exception):
    """Game-related error"""


class MasterRemote:
    """Master remote object."""

    def __init__(self):
        """Initialize."""
        self.remote_id = None


class ChainballGame:
    """Game engine."""

    def __init__(self, virtual_hw=False, remote_score=False):
        """Initialize."""
        self.logger = logging.getLogger("sboard.game")
        self._remotes = remote_score

        self.s_handler = ScoreHandler("/dev/ttyAMA0", virt_hw=virtual_hw)
        if self._remotes:
            self.rf_handler = NRF24Handler(fake_hw=virtual_hw)
            # load remote mapping configuration file
            self.remote_mapping = RemoteMapping("rm_map")
            try:
                remote_mapping_config = CHAINBALL_CONFIGURATION.retrieve_configuration(
                    "remotemap"
                )
                self.remote_mapping.parse_config(remote_mapping_config)
            except (RemoteMappingLoadFailed, ChainBallConfigurationError):
                self.logger.error("Failed to load remote button mapping")
                exit(1)
            # remote pair handler (non-threaded)
            self.pair_handler = RemotePairHandler(
                fail_cb=self.pair_fail, success_cb=self.pair_end
            )
        else:
            self.rf_handler = None
            self.remote_mapping = None
            self.pair_handler = None

        # load SFX mapping configuration file
        self.sfx_mapping = SFXMapping()
        try:
            sfx_mapping_config = CHAINBALL_CONFIGURATION.retrieve_configuration(
                "game"
            )
            self.sfx_mapping.parse_config(sfx_mapping_config)
        except SFXMappingLoadFailed:
            self.logger.error("Failed to load SFX mapping")

        # load other game configuration
        self.game_config = ChainballGameConfiguration()
        try:
            game_config = CHAINBALL_CONFIGURATION.retrieve_configuration("game")
            self.game_config.parse_config(game_config)
        except:
            self.logger.error("Failed to load game configuration")
            exit(1)

        # timer handler for RGB matrix
        self.timer_handler = TimerHandler(self.game_timeout, self)
        # timer handler for player panels
        self.ptimer_handler = TimerHandler(self.game_timeout, self, False)

        # create player dictionary
        self.players = {
            x: PlayerScore(
                self.game_config.serve_timeout,
                self.s_handler,
                x,
                autoadv_cb=self.game_pass_turn,
            )
            for x in range(4)
        }
        self.player_count = 0

        # game persistance
        db_configuration = CHAINBALL_CONFIGURATION.retrieve_configuration("db")
        persist_location = os.path.join(
            db_configuration["database_location"], "persist", "games"
        )
        self.g_persist = GamePersistance(persist_location)

        # set flags
        self.ongoing = False
        self.active_player = None
        self.game_uuid = None
        self.paused = False
        self.error = False
        self.score_display_ended = True
        self._next_uid = None

        if self.rf_handler is not None:
            # start rf handler
            self.rf_handler.start()

            # master remote
            self.m_remote = MasterRemote()
        else:
            self.m_remote = None

        # start score handler
        self.s_handler.start()

        # sound effects
        try:
            self.sfx_handler = GameSFXHandler()
        except Exception as ex:
            raise
            self.logger.error(
                "Failed to initialize SFX handler with: {}".format(ex)
            )

        # other variables
        self._current_fault_count = 0

    def post_init(self):
        """Post-initialization tasks."""
        self.timer_handler.announcement(
            TimerAnnouncement("CHAIN", "BALL", self.init_announcement_end), 10
        )

    def init_announcement_end(self):
        """Do setup after initialization announcement."""
        self.timer_handler.setup(20)

    def unpair_remote(self, player):
        """Unpair a players remote."""
        if self._remotes is False:
            raise ChainballGameError("remotes are disabled")

        if player not in self.players:
            raise KeyError("Invalid Player")

        if self.players[player].registered is False:
            raise PlayerNotRegisteredError("Player not registered")

        if self.players[player].remote_id is None:
            raise PlayerNotPairedError("Player not paired to a remote")

        self.logger.info(
            "Unpairing remote {} for player {}".format(
                self.players[player].remote_id, player
            )
        )

        self.pair_handler.stop_tracking(self.players[player].remote_id)
        self.players[player].remote_id = None

    def pair_master(self):
        """Pair master remote."""
        if self._remotes is False:
            raise ChainballGameError("remotes are disabled.")
        if self.m_remote.remote_id is not None:
            raise MasterRemoteAlreadyPairedError(
                "Already paired to {}".format(self.m_remote.remote_id)
            )
        # pair
        self.pair_handler.start_pair("master", self.game_config.pair_timeout)

    def unpair_master(self):
        """Unpair master remote."""
        if self._remotes is False:
            raise ChainballGameError("remotes are disaled.")
        self.pair_handler.stop_tracking(self.m_remote.remote_id)
        self.m_remote.remote_id = None

    def pair_remote(self, player):
        """Pair a players remote."""
        if self._remotes is False:
            raise ChainballGameError("remotes are disabled.")
        if player not in self.players:
            raise KeyError("Invalid player")

        if self.players[player].registered is False:
            raise PlayerNotRegisteredError("Player not registered")

        if self.players[player].remote_id:
            raise PlayerAlreadyPairedError(
                "Already paired to {}".format(self.players[player].remote_id)
            )

        # start pairing
        self.pair_handler.start_pair(player, self.game_config.pair_timeout)

    def pair_end(self, player, remote_id):
        """Finish pairing remote."""
        if self._remotes is False:
            raise ChainballGameError("remotes are disabled.")
        if player == "master":
            self.m_remote.remote_id = remote_id
            self.logger.info(
                "Paired remote {} as the master remote".format(remote_id)
            )
            return

        self.players[player].remote_id = remote_id
        self.logger.info(
            "Paired player {} to remote {}".format(
                player, self.players[player].remote_id
            )
        )

    def pair_fail(self, player, reason=None):
        """Remote pairing failed."""
        if reason == RemotePairFailureType.TIMEOUT:
            self.logger.info(
                "Pairing for player {}"
                " failed due to a timeout".format(player)
            )
        elif reason == RemotePairFailureType.ALREADY_PAIRED:
            self.logger.info(
                "Pairing for player {} "
                "failed: remote is already paired".format(player)
            )
        else:
            self.logger.info(
                "Pairing for player {}"
                "failed due to an unknown reason".format(player)
            )

    def pair_running(self):
        """Get if pairing is occurring."""
        if self._remotes is False:
            return ["DISABLED", None]
        if self.pair_handler.is_running():
            return ["PAIR", None]
        if self.pair_handler.has_failed() is not None:
            return ["FAIL", self.pair_handler.has_failed()]

        return ["IDLE", None]

    def shutdown(self):
        """Shutdown engine."""
        self.logger.debug("shutting down game engine")
        self.s_handler.stop()
        self.s_handler.join()
        if self._remotes:
            self.rf_handler.stop()
            self.rf_handler.join()
        self.logger.debug("game engine shutdown complete")

    def game_can_start(self):
        """Verify if game can be started."""
        # check that at least 2 players are registered
        if self.player_count < 2:
            return False

        # check that all players have paired remotes
        for player in self.players:
            if self.players[player].registered is False:
                continue
            if self._remotes:
                if self.players[player].remote_id is None:
                    return False

        return True

    def do_announcement(self, announcement, duration, dont_handle=False):
        """Perform an announcement."""
        if dont_handle is False:
            # save callback
            original_cb = announcement.cb

            # insert our callback
            announcement.cb = self.default_announcement_end
            announcement.cb_args = original_cb

        self.timer_handler.announcement(announcement, duration)

    def do_player_announcement(
        self, player_number, announcement, duration, dont_handle=False
    ):
        """Perform announcement in player panels."""
        if dont_handle is False:
            # save callback
            original_cb = announcement.cb

            # insert our callback
            announcement.cb = self.default_announcement_end
            announcement.cb_args = original_cb

        self.timer_handler.player_announcement(
            announcement, duration, player_number
        )

    def default_announcement_end(self, original_cb=None):
        """Post-announcement tasks."""
        if not self.ongoing:
            self.timer_handler.setup(20)

        # original callback
        if original_cb:
            original_cb()

    def register_players(self, player_texts):
        """Register players."""
        if self.ongoing:
            raise GameRunningError("Cant register players while running")

        if len(player_texts) > 4 - self.player_count:
            raise TooManyPlayersError("Limited to 4 players")

        for player in player_texts:
            if player > 3 or player < 0:
                # ignore this for now
                self.logger.debug("Invalid player, ignoring")
                continue

            if player in self.players:
                # ignore
                if self.players[player].registered:
                    self.logger.debug(
                        "Player {} is already registered, ignoring".format(
                            player
                        )
                    )
                    continue

            self.s_handler.register_player(
                player, player_texts[player].panel_txt
            )
            self.players[player].web_text = player_texts[player].web_txt
            self.players[player].panel_text = player_texts[player].panel_txt
            self.players[player].registered = True
            self.player_count += 1

            self.logger.debug("Registered player {}".format(player))

    def next_player_num(self):
        """Get next player id to be inserted."""
        for player in self.players:
            if self.players[player].registered is False:
                return player

        raise TooManyPlayersError

    def _reorganize_players(self):
        for p_id, p_data in self.players.items():
            if p_data.registered is False:

                # empty slot, move up other players if available
                for p_num in range(p_id + 1, 4):
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
        """Unregister players."""
        if self.ongoing:
            raise GameRunningError("cant unregister players while running")

        for player in players:
            if player not in self.players:
                # ignore
                continue

            if self.players[player].registered is False:
                # ignore
                continue

            self.s_handler.unregister_player(player)
            self.players[player].web_text = None
            self.players[player].panel_text = None
            self.players[player].registered = False
            if self.pair_handler is not None:
                self.pair_handler.stop_tracking(self.players[player].remote_id)
            self.players[player].remote_id = None
            self.player_count -= 1

        self._reorganize_players()

    def game_begin(self):
        """Start the game."""
        # flush remote message queue for good measure
        if self.rf_handler is not None:
            self.rf_handler.flush_message_queue()

        self.logger.info("Starting game...")
        if self.ongoing:
            raise GameAlreadyStarterError("Game is running")

        if self.player_count < 2:
            raise NotEnoughPlayersError("Game needs at least 2 players")

        # check if remotes are paired
        for player in self.players:
            if (
                self.players[player].remote_id is None
                and self.players[player].registered
            ):
                raise PlayerRemoteNotPaired(
                    "Player {} has no remote paired".format(player)
                )

        # reorder players
        self._reorganize_players()

        # clear scores and prepare data
        player_persist = {}
        for player in self.players:
            if self.players[player].registered:
                self.game_set_score(player, 0)
                player_persist[player] = PlayerPersistData(
                    self.players[player].panel_text,
                    self.players[player].web_text,
                )
                self.players[player].reset_serve()

        # create persistance data
        self.game_uuid = self.g_persist.new_record(
            player_persist, self._next_uid
        )

        # flag game start
        self.ongoing = True
        self.paused = False
        self.game_set_active_player(0)

        self.timer_handler.start(self.game_config.game_duration)
        self.ptimer_handler.start(self.game_config.game_duration)

        # confirm start
        self.g_persist.start_game(self.get_remaining_time())

        self.timer_handler.announcement(TimerAnnouncement("Game", "START"), 2)
        self.logger.info("Game started")

    def set_game_uid(self, game_uid):
        """Set game uid."""
        if self.ongoing is False:
            # set next game's uid.
            self._next_uid = game_uid
        else:
            self.g_persist.assign_user_id(game_uid)

    def get_remaining_time(self):
        """Get remaining time in seconds."""
        if self.ongoing is False:
            return None

        minutes, seconds = self.timer_handler.get_remaining_time()

        return minutes * 60 + seconds

    def get_running_time(self):
        """Get running time in seconds."""
        if self.ongoing is False:
            return None

        # duration in seconds
        duration = self.game_config.game_duration * 60

        return duration - self.get_remaining_time()

    def find_high_score(self):
        """Find high score between players."""
        winner_score = -10
        winner_player = 0
        for player in self.players:
            if self.players[player].current_score > winner_score:
                winner_player = player
                winner_score = self.players[player].current_score

        return winner_player

    def game_timeout(self):
        """Game timeout occured."""
        self.logger.info("Game has run out of time")
        self.game_end(reason="TIMEOUT", winner=self.find_high_score())

    def game_pause(self):
        """Pause game."""
        if not self.ongoing:
            raise GameNotStartedError("game is not running")

        if self.paused:
            raise GameAlreadyPausedError("game is already paused")

        self.g_persist.pause_unpause_game()

        self.logger.info("Game PAUSED")
        self.paused = True
        self.timer_handler.pause()
        self.ptimer_handler.pause()

    def game_unpause(self):
        """Unpause game."""
        if not self.ongoing:
            raise GameNotStartedError("game is not running")

        if not self.paused:
            raise GameNotPausedError("game is not paused")

        # check if all remotes are paired
        for p_id, p_data in self.players.items():
            if p_data.registered and p_data.remote_id is None:
                # registered but unpaired
                raise PlayerRemoteNotPaired(
                    "Player {} has no remote paired".format(p_id)
                )

        self.g_persist.pause_unpause_game()

        self.logger.info("Game UNPAUSED")
        self.paused = False
        self.timer_handler.unpause()
        self.ptimer_handler.unpause()

    def game_end(self, reason=None, winner=None):
        """Stop game."""
        self.logger.info("Stopping game...")
        if not self.ongoing:
            raise GameNotStartedError("Game is not running")

        winner_player = self.find_high_score()

        self.s_handler.set_turn(winner_player)
        self.announce_end(winner_player)

        # play sfx
        try:
            game_end_sfx = self.sfx_mapping.get_sfx(SFXMappableEvents.GAME_END)
            self.sfx_handler.play_fx(game_end_sfx)
        except SFXUnknownEvent:
            pass

        self.timer_handler.stop()
        self.ptimer_handler.stop()

        self.g_persist.end_game(
            reason, winner, self.get_running_time(), self.get_remaining_time()
        )

        self.ongoing = False
        self.game_uuid = None
        self._next_uid = None

        self.logger.info("Game stopped")

    def game_set_active_player(self, player):
        """Set active player."""
        if not self.ongoing:
            raise GameNotStartedError("Game is not running")

        # see if player is registered
        if self.players[player].registered is False:
            raise PlayerNotRegisteredError("Player is not taking part in game")

        for p in self.players:
            self.players[p].score_diff = 0
            if p == player:
                self.players[p].is_turn = True
                self.active_player = p
            else:
                self.players[p].is_turn = False

    def announce_player_deltas(self, player):
        """Announce score difference in relation to last serve."""
        if player > self.player_count - 1:
            return

        if player not in self.players:
            return

        # don't announce players with zero score delta
        for p in range(player, self.player_count):
            if (
                self.players[p].score_diff == 0
                or self.players[p].current_score == -10
            ):
                continue
            else:
                self.timer_handler.announcement(
                    TimerAnnouncement(
                        self.players[p].panel_text,
                        "{:+1d}".format(self.players[p].score_diff),
                    ),
                    2,
                )

    def game_pass_turn(self, force_serve=False):
        """Force serve, pass turn."""
        if not self.ongoing:
            raise GameNotStartedError("Game is not running")

        # reset all serves immediately
        self.logger.debug("Resetting serve states")
        for player in self.players:
            self.players[player].reset_serve()

        # create event in persistance
        if force_serve is True:
            self.g_persist.log_event(
                GameEventTypes.FORCE_SERVE,
                {
                    "player": int(self.active_player),
                    "gtime": self.get_running_time(),
                },
            )

        # announce score deltas
        self.announce_player_deltas(0)

        next_player = None
        for p in range(self.active_player + 1, self.player_count):
            if self.players[p].current_score != -10:
                self.game_set_active_player(p)
                next_player = p
                break

        if next_player is None:
            # reaching here, begin at player 0 score
            for p in range(0, self.active_player):
                if self.players[p].current_score != -10:
                    self.game_set_active_player(p)
                    next_player = p
                    break

        if force_serve is False:
            self.g_persist.log_event(
                GameEventTypes.SERVE_ADVANCE,
                {"player": int(p), "gtime": self.get_running_time()},
            )

    def game_player_out(self, player):
        """Cowout callback."""
        # play sound here, announce
        self.logger.debug("Player {} is out of the game!".format(player))

        self.timer_handler.announcement(
            TimerAnnouncement(self.players[player].panel_text, "COWOUT"), 4
        )

        try:
            cowout_sfx = self.sfx_mapping.get_sfx(SFXMappableEvents.COW_OUT)
            self.sfx_handler.play_fx(cowout_sfx)
        except SFXUnknownEvent:
            self.logger.warning("SFX play error")

    def game_decrement_score(self, player, referee_event=False):
        """Decrement a players score."""
        if player is None:
            return

        if not self.players[player].registered:
            return

        if self.paused or not self.ongoing:
            return

        if (
            self.players[player].current_score > -10
            and self.players[player].score_diff > -2
        ):
            self.players[player].current_score -= 1
            self.players[player].score_diff -= 1

            # update persistance data
            self.g_persist.update_current_score(
                player,
                self.players[player].current_score,
                forced_update=referee_event,
                game_time=self.get_running_time(),
            )

            # check here if we have reached -10
            if self.players[player].current_score == -10:
                # player is out of the game
                self.g_persist.log_event(
                    GameEventTypes.COWOUT,
                    {"player": player, "gtime": self.get_running_time()},
                )
                return

    def game_increment_score(self, player, referee_event=False):
        """Increment a players score."""
        if player is None:
            return

        if not self.players[player].registered:
            return

        if self.paused or not self.ongoing:
            return

        if (
            self.players[player].current_score < 5
            and self.players[player].score_diff < 2
        ):
            self.players[player].current_score += 1
            self.players[player].score_diff += 1

            # update persistance data
            self.g_persist.update_current_score(
                player,
                self.players[player].current_score,
                forced_update=referee_event,
                game_time=self.get_running_time(),
            )

    def game_force_score(self, player, score):
        """Force scores."""
        self.players[player].force_score(score)

        if self.ongoing is True:
            # update persistance data
            self.g_persist.force_current_score(
                player, score, game_time=self.get_running_time()
            )

    def game_set_score(self, player, score):
        """Set scores."""
        self.players[player].current_score = score

        if self.ongoing is True:
            # update persistance data
            self.g_persist.update_current_score(
                player,
                score,
                forced_update=False,
                game_time=self.get_running_time(),
            )

    def _game_decode_remote(self, message):
        # handle pairing
        if self.pair_handler.remote_event(message):
            return

        # master
        if message.remote_id == self.m_remote.remote_id:
            # master remote actions
            if message.command == RemoteCommands.BTN_PRESS:
                if (
                    self.remote_mapping.master_mapping[message.cmd_data]
                    == MasterRemoteActions.PAUSE_UNPAUSE_CLOCK
                ):
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

        if self.paused:
            return

        commanding_player = self.find_player_by_remote(message.remote_id)

        mapping = self.remote_mapping.player_mapping[message.cmd_data]
        if message.command == RemoteCommands.BTN_PRESS:
            if mapping == GameTurnActions.DECREASE_SCORE:
                self.game_decrement_score(commanding_player)
            elif mapping == GameTurnActions.INCREASE_SCORE:
                self.game_increment_score(commanding_player)
            elif mapping == GameTurnActions.PASS_TURN:
                if (
                    message.remote_id
                    != self.players[self.active_player].remote_id
                ):
                    self.logger.debug(
                        "Only the active player can force the serve"
                    )
                    return
                self.game_pass_turn(force_serve=True)

    def find_player_by_remote(self, remote_id):
        """Find player by remote id."""
        for player in self.players:
            if self.players[player].remote_id == remote_id:
                return player

    def count_players_out(self):
        """Get how many players are out of the game."""
        players_out = 0
        for player in self.players:
            if self.players[player].current_score == -10:
                players_out += 1

        return players_out

    def game_swap_players(self, players):
        """Swap players."""
        return

    def announce_end(self, winner):
        """Announce game end, winner."""
        self.do_announcement(
            TimerAnnouncement(
                self.players[winner].panel_text, "WINS!", self.force_show_clock
            ),
            10,
            True,
        )

    def force_show_clock(self):
        """Force matrix to refresh."""
        self.timer_handler.refresh_matrix()

    def end_score_display(self):
        """Show score at end."""
        self.score_display_ended = True

    def scoring_evt(self, player, evt_type):
        """Process scoring events."""
        if self.ongoing is False:
            return

        if evt_type == "deadball":
            self.g_persist.log_event(
                GameEventTypes.DEADBALL,
                {"player": int(player), "gtime": self.get_running_time()},
            )
            self.game_pass_turn()
        elif evt_type == "chainball":
            self.g_persist.log_event(
                GameEventTypes.CHAINBALL,
                {"player": int(player), "gtime": self.get_running_time()},
            )
            self.game_increment_score(int(player), referee_event=True)
        elif evt_type == "jailbreak":
            self.g_persist.log_event(
                GameEventTypes.JAILBREAK,
                {"player": int(player), "gtime": self.get_running_time()},
            )
            self.game_increment_score(int(player), referee_event=True)
            self.game_increment_score(int(player), referee_event=True)
        elif evt_type == "ratmeat":
            self.g_persist.log_event(
                GameEventTypes.BALL_HIT,
                {"player": int(player), "gtime": self.get_running_time()},
            )
            self.game_decrement_score(int(player), referee_event=True)
        elif evt_type == "mudskipper":
            self.g_persist.log_event(
                GameEventTypes.MUDSKIPPER,
                {"player": int(player), "gtime": self.get_running_time()},
            )
            self.game_decrement_score(int(player), referee_event=True)
        elif evt_type == "sailormoon":
            self.g_persist.log_event(
                GameEventTypes.SAILORMOON,
                {"player": int(player), "gtime": self.get_running_time()},
            )
            self.game_decrement_score(int(player), referee_event=True)
            self.game_decrement_score(int(player), referee_event=True)
        elif evt_type == "fault":
            if self._current_fault_count == 0:
                self.g_persist.log_event(
                    GameEventTypes.FAULT,
                    {"player": int(player), "gtime": self.get_running_time()},
                )
                self._current_fault_count = 1
            elif self._current_fault_count == 1:
                self.g_persist.log_event(
                    GameEventTypes.DOUBLEFAULT,
                    {"player": int(player), "gtime": self.get_running_time()},
                )
                self.game_decrement_score(int(player), referee_event=True)
                # reset count immediately
                self._current_fault_count = 0
        elif evt_type == "doublefault":
            self.g_persist.log_event(
                GameEventTypes.DOUBLEFAULT,
                {"player": int(player), "gtime": self.get_running_time()},
            )
            self.game_decrement_score(int(player), referee_event=True)
        elif evt_type == "slowpoke":
            self.g_persist.log_event(
                GameEventTypes.SLOWPOKE,
                {"player": int(player), "gtime": self.get_running_time()},
            )
            self.game_decrement_score(int(player), referee_event=True)

    def game_loop(self):
        """Handle main game loop."""
        # handle serves
        if self.ongoing:
            for player in self.players:
                self.players[player].handle_serve()

        # handle SFX
        self.sfx_handler.handle()

        # handle pairing
        if self.pair_handler is not None:
            self.pair_handler.handle()

        # handle timer
        self.timer_handler.handle()

        # handle player panel timer
        self.ptimer_handler.handle()

        # check for a cowout
        if self.ongoing:
            for player in self.players:
                if (
                    self.players[player].current_score == -10
                    and self.players[player].is_cowout is False
                ):
                    self.players[player].is_cowout = True
                    self.game_player_out(player)

        # check for a winner
        if self.ongoing:
            if self.count_players_out() >= self.player_count - 1:
                self.logger.info("Only one player remais! Ending")
                self.game_timeout()
                return

            for player in self.players:
                if self.players[player].current_score == 5:
                    self.logger.info(
                        "Player {} has won the game".format(player)
                    )
                    self.announce_end(player)
                    self.game_end(reason="PLAYER_WON", winner=player)
                    return

        # check for remote activity
        if self.rf_handler is not None and self.rf_handler.message_pending():
            message = self.rf_handler.receive_message()
            # process message
            try:
                decoded = RemoteDecoder(message.payload)
            except IOError:
                # invalid, ignore
                return

            self.logger.debug("Received: {}".format(decoded))
            self._game_decode_remote(decoded)

        # make score announcements
        if self.score_display_ended and self.ongoing:
            self.score_display_ended = False
            for p in self.players:
                if p > self.player_count - 1:
                    continue
                if p == self.player_count - 1:
                    callback = self.end_score_display
                else:
                    callback = None
                self.ptimer_handler.player_announcement(
                    TimerAnnouncement(
                        "",
                        "{:+1d}".format(self.players[p].current_score),
                        callback,
                    ),
                    5,
                    p,
                )
