import struct
import time
import logging
import json

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


class RemotePersistence(object):

    def __init__(self, persistence_file):

        self.pfile = persistence_file

        try:
            with open(persistence_file, 'r') as f:
                self.remote_list = json.load(f)
        except:
            self.remote_list = {}

    def _do_save(self):
        with open(self.pfile, 'w') as f:
            json.dump(self.remote_list, f)

    def is_known(self, remote_id):
        return hex(remote_id) in self.remote_list

    def add_remote(self, remote_id, data=None):
        self.remote_list[hex(remote_id)] = data
        self._do_save()

    def upd_data(self, remote_id, data):
        self.remote_list[hex(remote_id)] = data
        self._do_save()

PERSISTENT_REMOTE_DATA = RemotePersistence('conf/remote.json')

class RemoteCommands(object):

    BTN_PRESS = 2
    BTN_RELEASE = 1
    BATT = 3

class RemoteDecoder(object):

    def __init__(self, message):

        self.remote_id, self.command, self.cmd_data = self.decode(message)

    @classmethod
    def decode(cls, message):

        buf = "".join([chr(x) for x in message])
        remote_id = struct.unpack_from('I', buf, 0)[0]
        command = message[4]
        command_data = message[5]

        if remote_id == 0:
            raise IOError('Invalid message')

        #persistence hack
        if PERSISTENT_REMOTE_DATA.is_known(remote_id):
            if command == RemoteCommands.BATT:
                #update last known battery level
                PERSISTENT_REMOTE_DATA.upd_data(remote_id, command_data)
        else:
            if command == RemoteCommands.BATT:
                save_data = command_data
            else:
                save_data = None
            PERSISTENT_REMOTE_DATA.add_remote(remote_id, save_data)

        return remote_id, command, command_data

    def __repr__(self):

        if self.command == RemoteCommands.BATT:
            return "remote({}): BATT -> {}%".format(hex(self.remote_id), self.cmd_data)

        ret = "remote({}): BTN({}) ".format(hex(self.remote_id), self.cmd_data)

        if self.command == RemoteCommands.BTN_PRESS:
            ret += "pressed"
        elif self.command == RemoteCommands.BTN_RELEASE:
            ret += "released"

        return ret
