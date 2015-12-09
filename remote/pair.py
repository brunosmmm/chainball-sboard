import time
import logging
from remote.constants import RemotePairStates, RemotePairFailureType, PAIRING_TIMEOUT

class RemotePairHandler(object):

    def __init__(self, fail_cb=None, success_cb=None):
        self.logger = logging.getLogger('sboard.pairHandler')
        self.state = RemotePairStates.IDLE
        self.player_pair = None
        self.timer = None
        self.timeout = None
        self.fail_callback = fail_cb
        self.success_callback = success_cb
        self.fail_reason = None
        self.pair_track = {}

    def start_pair(self, player, timeout=PAIRING_TIMEOUT):
        self.logger.info('Pairing remote for player {}'.format(player))
        self.timer = time.time()
        self.timeout = timeout
        self.player_pair = player
        self.fail_reason = None
        self.state = RemotePairStates.RUNNING

    def stop_tracking(self, remote_id):
        if remote_id in self.pair_track.keys():
            del self.pair_track[remote_id]

    def is_running(self):
        return self.state == RemotePairStates.RUNNING

    def has_failed(self):
        if self.state == RemotePairStates.ERROR:
            return self.fail_reason
        else:
            return None

    def remote_event(self, message):
        if self.state == RemotePairStates.RUNNING:
            if message.remote_id in self.pair_track.keys():
                #remote already paired
                self.state = RemotePairStates.ERROR
                self.fail_reason = RemotePairFailureType.ALREADY_PAIRED
                if self.fail_callback:
                    self.fail_callback(self.player_pair, RemotePairFailureType.ALREADY_PAIRED)
            else:
                #track pairing
                self.pair_track[message.remote_id] = self.player_pair
                #clean
                self.timer = None
                #callback
                if self.success_callback:
                    self.success_callback(self.player_pair, message.remote_id)
                #pairing succeeded
                self.player_pair = None
                self.state = RemotePairStates.IDLE
            return True
        return False

    def handle(self):
        if self.state == RemotePairStates.IDLE:
            return

        if self.state == RemotePairStates.RUNNING:
            #check timeout
            if time.time() - self.timer > self.timeout:
                self.state = RemotePairStates.ERROR
                self.fail_reason = RemotePairFailureType.TIMEOUT
                #failure callback
                if self.fail_callback:
                    self.fail_callback(self.player_pair, RemotePairFailureType.TIMEOUT)
