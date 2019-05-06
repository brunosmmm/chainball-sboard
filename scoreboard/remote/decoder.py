"""Remote decoder."""

from remote.constants import RemoteCommands
from remote.persistence import PERSISTENT_REMOTE_DATA
import struct


class RemoteDecoder(object):
    """Decoder class."""

    def __init__(self, message):
        """Iniialize."""
        self.remote_id, self.command, self.cmd_data = self.decode(message)

    @classmethod
    def decode(cls, message):
        """Decode message."""
        buf = "".join([chr(x) for x in message])
        remote_id = struct.unpack_from("I", buf, 0)[0]
        command = message[4]
        command_data = message[5]

        if remote_id == 0:
            raise IOError("Invalid message")

        # persistence hack
        if PERSISTENT_REMOTE_DATA.is_known(remote_id):
            if command == RemoteCommands.BATT:
                # update last known battery level
                PERSISTENT_REMOTE_DATA.upd_data(remote_id, command_data)
        else:
            if command == RemoteCommands.BATT:
                save_data = command_data
            else:
                save_data = None
            PERSISTENT_REMOTE_DATA.add_remote(remote_id, save_data)

        return remote_id, command, command_data

    def __repr__(self):
        """Dump strings."""
        if self.command == RemoteCommands.BATT:
            return "remote({}): BATT -> {}%".format(hex(self.remote_id), self.cmd_data)

        ret = "remote({}): BTN({}) ".format(hex(self.remote_id), self.cmd_data)

        if self.command == RemoteCommands.BTN_PRESS:
            ret += "pressed"
        elif self.command == RemoteCommands.BTN_RELEASE:
            ret += "released"

        return ret
