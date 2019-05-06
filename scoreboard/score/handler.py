"""Score display handler."""

import time
import logging
import struct
from util.threads import StoppableThread
import threading
import serial
from score.constants import PlayerScoreCommands, PlayerScoreConstraints
from score.exceptions import TextTooBigError

try:
    import Queue
except ImportError:
    # python3
    import queue as Queue
import os
import pty


class ScoreUpdateEventTypes(object):
    """Update event types."""

    SCORE_UPD = 1
    SET_TURN = 2
    SET_MODE = 3
    SET_TEXT = 4
    TURN_OFF = 5
    BLINK_SCORE = 6


class ScoreUpdateEvent(object):
    """Update event."""

    def __init__(self, upd_type, data):
        """Initialize."""
        self.upd_type = upd_type
        self.data = data


class ScoreHandler(StoppableThread):
    """Score handler."""

    def __init__(self, serial_port, serial_baud=38400, virt_hw=False):
        """Initialize."""
        super(ScoreHandler, self).__init__()

        self.serial_port = serial_port
        self.serial_baud = serial_baud
        self.logger = logging.getLogger("sboard.scoreHandler")

        # open serial connection
        self.logger.debug("Opening serial port: {}".format(self.serial_port))
        try:
            if virt_hw is False:
                self.ser_port = serial.Serial(self.serial_port, self.serial_baud)
            else:
                self.master_port, self.slave_port = pty.openpty()
                self.ser_port = serial.Serial(
                    os.ttyname(self.slave_port),
                    self.serial_baud,
                    rtscts=True,
                    dsrdtr=True,
                )
        except IOError:
            print("Can't open serial port")
            raise

        # event queue
        self.evt_q = Queue.Queue()

        # running flag
        self.is_running = threading.Event()

    def _write_score(self, player, score):
        buf = struct.pack(
            "4s",
            bytes([player, PlayerScoreCommands.SCORE, score, PlayerScoreCommands.TERM]),
        )
        self.ser_port.write(buf)

    def _clear_score(self, player):
        self.logger.debug("issuing CLR to player {}".format(player))
        buf = struct.pack(
            "3s", bytes([player, PlayerScoreCommands.CLR, PlayerScoreCommands.TERM])
        )
        self.ser_port.write(buf)

    def _set_turn(self, player):
        buf = struct.pack(
            "3s", bytes([player, PlayerScoreCommands.TURN, PlayerScoreCommands.TERM])
        )
        self.ser_port.write(buf)

    def _set_text(self, player, text):
        self.logger.debug("setting text: player {} -> {}".format(player, text))
        buf = struct.pack(
            "ccc{}sc".format(len(text)),
            bytes([player]),
            bytes([PlayerScoreCommands.DATA]),
            bytes([len(text)]),
            text.encode(),
            bytes([PlayerScoreCommands.TERM]),
        )
        self.ser_port.write(buf)

    def _set_mode(self, player, mode):
        buf = struct.pack(
            "4s",
            bytes([player, PlayerScoreCommands.MODE, mode, PlayerScoreCommands.TERM]),
        )
        self.ser_port.write(buf)

    def _set_blink(self, player, bitfield):
        buf = struct.pack(
            "cccc",
            bytes(
                [player, PlayerScoreCommands.BLINK, bitfield, PlayerScoreCommands.TERM]
            ),
        )
        self.ser_port.write(buf)

    @classmethod
    def check_score_bounds(cls, score):
        """Verify if score is valid."""
        if score < -10 or score > 5:
            return False

        return True

    def blink_start(self, player, fast=False):
        """Start blinking player score."""
        self.logger.debug("Setting player {} score to blink".format(player))

        # enable blinking
        bitfield = 0x01
        if fast:
            bitfield |= 0x02

        self.evt_q.put(
            ScoreUpdateEvent(ScoreUpdateEventTypes.BLINK_SCORE, [player, bitfield])
        )

    def blink_stop(self, player, enable=True):
        """Stop blinking."""
        self.logger.debug("Stopping score blinking for player {}".format(player))

        # disable blinking
        bitfield = 0x00
        if enable:
            bitfield |= 0x04

        self.evt_q.put(
            ScoreUpdateEvent(ScoreUpdateEventTypes.BLINK_SCORE, [player, bitfield])
        )

    def update_score(self, player, score):
        """Update score."""
        self.logger.info("Updating player {} score to {}".format(player, score))
        if not self.check_score_bounds(score):
            raise ValueError("Invalid score value")

        self.evt_q.put(
            ScoreUpdateEvent(ScoreUpdateEventTypes.SCORE_UPD, [player, score + 10])
        )

    def set_turn(self, player):
        """Set active turn."""
        self.logger.info("Switching to player {} turn".format(player))
        self.evt_q.put(ScoreUpdateEvent(ScoreUpdateEventTypes.SET_TURN, [player]))

    # backwards compatibility
    def register_player(self, player, text):
        """Register player."""
        self.set_panel_text(player, text)

    def set_panel_text(self, player, text):
        """Set display panel text."""
        if text is None:
            return

        if len(text) > PlayerScoreConstraints.LARGE_TEXT_MAX_LEN:
            if len(text) > PlayerScoreConstraints.SMALL_TEXT_MAX_LEN:
                raise TextTooBigError("Player text is too big")
            self.evt_q.put(
                ScoreUpdateEvent(ScoreUpdateEventTypes.SET_MODE, [player, 0])
            )
        else:
            self.evt_q.put(
                ScoreUpdateEvent(ScoreUpdateEventTypes.SET_MODE, [player, 1])
            )

        # write text
        self.evt_q.put(ScoreUpdateEvent(ScoreUpdateEventTypes.SET_TEXT, [player, text]))

    def unregister_player(self, player):
        """Unregister player."""
        self.evt_q.put(ScoreUpdateEvent(ScoreUpdateEventTypes.TURN_OFF, [player]))

    def process_queue(self):
        """Process display command queue."""
        if not self.evt_q.empty():

            evt = self.evt_q.get()

            if evt.upd_type == ScoreUpdateEventTypes.SCORE_UPD:
                if len(evt.data) != 2:
                    # ignore
                    return

                # set score
                self._write_score(*evt.data)

            elif evt.upd_type == ScoreUpdateEventTypes.SET_TURN:
                if len(evt.data) != 1:
                    # ignore
                    return

                self._set_turn(evt.data[0])

            elif evt.upd_type == ScoreUpdateEventTypes.SET_MODE:
                if len(evt.data) != 2:
                    return

                self._set_mode(*evt.data)

            elif evt.upd_type == ScoreUpdateEventTypes.SET_TEXT:
                if len(evt.data) != 2:
                    return

                self._set_text(*evt.data)

            elif evt.upd_type == ScoreUpdateEventTypes.TURN_OFF:
                if len(evt.data) != 1:
                    return

                self._clear_score(evt.data[0])

            elif evt.upd_type == ScoreUpdateEventTypes.BLINK_SCORE:
                if len(evt.data) != 2:
                    return

                self._set_blink(*evt.data)

    def run(self):
        """Run thread."""
        # initialize
        self._clear_score(0xFF)
        # set turn to inexistent player
        self._set_turn(0xFE)

        self.is_running.set()

        while True:

            if self.is_stopped():

                self.is_running.clear()
                exit(0)

            self.process_queue()

            # throttle cycle
            time.sleep(0.01)
