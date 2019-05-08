"""Serial LED Matrix controller."""

import serial
import struct
import time
import logging


class CommandType:
    """Matrix command types."""

    TEXT = 0
    SETPIXEL = 1
    CIRCLE = 2
    LINE = 3
    FILL = 4
    RECT = 5
    CLEAR = 6
    BEGIN = 7
    END = 8


class Color:
    """Matrix colors."""

    def __init__(self, r, g, b):
        """Initialize."""
        self.r = r
        self.g = g
        self.b = b

    def to_list(self):
        """Get value as list."""
        return [self.r, self.g, self.b]


class Coordinate:
    """Matrix coordinates."""

    def __init__(self, x, y):
        """Initialize."""
        self.x = x
        self.y = y


class SerialMessage:
    """Serial command or message."""

    def __init__(self, command, data):
        """Initialize."""
        self.command = command
        self.data = data


class MatrixControllerSerial:
    """Matrix controller."""

    def __init__(self, serport):
        """Initialize."""
        self.logger = logging.getLogger("sboard.matrixSer")

        try:
            self.ser_port = serial.Serial(serport, 115200)
            time.sleep(3)
        except:
            self.logger.warning("Timer matrix not present")
            self.ser_port = None

        self.do_group = None
        self.message_buffer = []

    def group_messages(self, amount):
        """Set message group size."""
        self.do_group = amount

    def _send_message(self, msg):

        bunch = False
        if self.do_group is not None:
            if self.do_group > 0:
                self.message_buffer.append(msg)
                self.do_group -= 1
                if self.do_group == 0:
                    bunch = True
                else:
                    return
            else:
                bunch = True

        if bunch:
            to_send = self.message_buffer[:]
            self.message_buffer = []
            self.do_group = None
        else:
            to_send = [msg]

        msg_buf = bytes()
        for message in to_send:
            section = bytes()
            section += struct.pack("c", bytes([message.command]))

            for part in message.data:
                if isinstance(part, int):
                    section += struct.pack("c", bytes([part & 0xFF]))
                elif isinstance(part, str):
                    section += struct.pack("c", bytes([len(part)]))
                    section += part.encode()
                elif isinstance(part, Color):
                    r, g, b = part.to_list()
                    section += struct.pack(
                        "ccc", bytes([r]), bytes([g]), bytes([b])
                    )
                elif isinstance(part, bool):
                    section += struct.pack(
                        "c", bytes([1]) if part else bytes([0])
                    )

            section = struct.pack("c", bytes([len(section) + 2])) + section
            section += struct.pack("c", bytes([0xFF]))

            msg_buf += section

        if self.ser_port is not None:
            self.ser_port.write(msg_buf)

    def setPixel(self, x, y, color):
        """Set a pixel value in the matrix."""
        message = SerialMessage(CommandType.SETPIXEL, [x, y, color])
        self._send_message(message)

    def putText(self, color, x, y, text, font, clear=False):
        """Draw text in the matrix."""
        message = SerialMessage(
            CommandType.TEXT, [x, y, color, text, font, clear]
        )
        self._send_message(message)

    def fill(self, color):
        """Fill matrix."""
        message = SerialMessage(CommandType.FILL, [color])
        self._send_message(message)

    def clear(self):
        """Clear matrix."""
        message = SerialMessage(CommandType.CLEAR, [])
        self._send_message(message)

    def begin_screen(self):
        """Start screen command."""
        message = SerialMessage(CommandType.BEGIN, [])
        self._send_message(message)

    def end_screen(self):
        """End screen command."""
        message = SerialMessage(CommandType.END, [])
        self._send_message(message)
