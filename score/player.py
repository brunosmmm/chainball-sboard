import logging
import time
from score.constants import PlayerServeStates, PLAYER_SERVE_SCORE_TIMEOUT

class PlayerScore(object):

    def __init__(self, handler=None, player_id=None, remote_id=None, autoadv_cb=None):

        self.initialized = False

        self.logger = logging.getLogger('sboard.score_{}'.format(player_id))

        self.handler = handler
        self.pid = player_id
        self.current_score = 0
        self.score_diff = 0
        self.is_turn = False
        self.web_text = None
        self.panel_text = None
        self.registered = False
        self.remote_id = remote_id

        self.serve_state = PlayerServeStates.IDLE
        self.score_start_timer = None
        self.autoadvance_callback = autoadv_cb
        self.is_cowout = False

        self.initialized = True

        # guard attribute score setting
        self.forcing_score = False

    @classmethod
    def _score_offset(cls, score):
        return score + 10

    def copy(self, other_player):
        self.current_score = other_player.current_score
        self.is_turn = other_player.is_turn
        self.web_text = other_player.web_text[:]
        self.panel_text = other_player.panel_text[:]
        self.remote_id = other_player.remote_id
        self.pid = other_player.pid

    def __setattr__(self, name, value):

        super(PlayerScore, self).__setattr__(name, value)

        #dont set values in __init__
        if self.initialized == False:
            return

        if name == "is_turn":
            if self.handler and self.is_turn:
                self.handler.set_turn(self.pid)
                self.start_serve()
            else:
                self.end_serve()

        elif name == "current_score":
            self._set_score(self.forcing_score)

        elif name == "panel_text":
            if self.handler and self.panel_text:
                self.handler.register_player(self.pid, self.panel_text)

    def force_score(self, new_score):
        self.forcing_score = True
        self.current_score = new_score
        self.forcing_score = False

    def _set_score(self, forced_update=False):
        if self.handler and self.current_score is not None:
            self.handler.update_score(self.pid, self.current_score)
            if forced_update is False:
                # enforce scoring window, pass serve automatically
                self.start_score()
            else:
                self.logger.debug('Forcing player {} score to {}'.format(self.pid, self.current_score))

    def show_text(self, text):
        self.handler.set_panel_text(self.pid, text)

    def restore_text(self):
        self.handler.set_panel_text(self.pid, self.panel_text)

    def start_serve(self):
        self.logger.debug('Player {} serving'.format(self.pid))
        self.serve_state = PlayerServeStates.SERVING

    def end_serve(self):
        if self.serve_state == PlayerServeStates.SERVING or self.serve_state == PlayerServeStates.SCORED:
            self.serve_state = PlayerServeStates.FINISHED

    def start_score(self):
        if self.serve_state != PlayerServeStates.SCORED:
            self.logger.debug('Player {} scored; scoring window closes in 3 seconds'.format(self.pid))
            self.score_start_timer = time.time()
            self.serve_state = PlayerServeStates.SCORED

    def reset_serve(self):
        self.serve_state = PlayerServeStates.IDLE
        self.score_start_timer = None

    def handle_serve(self):
        if self.serve_state == PlayerServeStates.IDLE:
            return

        if self.serve_state == PlayerServeStates.FINISHED:
            self.serve_state = PlayerServeStates.IDLE
            self.score_start_timer = None
            return

        if self.serve_state == PlayerServeStates.SCORED:
            if time.time() - self.score_start_timer > PLAYER_SERVE_SCORE_TIMEOUT:
                #autoadvance
                self.logger.debug('Scoring window closed for player {}, advancing'.format(self.pid))
                if self.autoadvance_callback:
                    self.autoadvance_callback()
                self.serve_state = PlayerServeStates.FINISHED
