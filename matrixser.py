import serial
import struct
import time
import logging

class CommandType(object):
    TEXT = 0
    SETPIXEL = 1
    CIRCLE = 2
    LINE = 3
    FILL = 4
    RECT = 5
    CLEAR = 6
    BEGIN = 7
    END = 8

class Color(object):
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def to_list(self):
        return [self.r, self.g, self.b]

class Coordinate(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

class SerialMessage(object):
    def __init__(self, command, data):
        self.command = command
        self.data = data

class MatrixControllerSerial(object):
    def __init__(self, serport):

        self.logger = logging.getLogger('sboard.matrixSer')

        try:
            self.ser_port= serial.Serial(serport, 115200)
            time.sleep(3)
        except:
            self.logger.warning('Timer matrix not present')
            self.ser_port = None

        self.do_group = None
        self.message_buffer = []

    def group_messages(self, amount):
        self.do_group = amount

    def _send_message(self, msg):

        bunch = False
        if self.do_group != None:
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

        msg_buf = ''
        for message in to_send:
            section = ''
            section += struct.pack('c', chr(message.command))

            for part in message.data:
                if isinstance(part, int):
                    section += struct.pack('c', chr(part & 0xFF))
                elif isinstance(part, str):
                    section += struct.pack('c', chr(len(part)))
                    section += part
                elif isinstance(part, Color):
                    r, g, b = part.to_list()
                    section += struct.pack('ccc', chr(r), chr(g), chr(b))
                elif isinstance(part, bool):
                    section += struct.pack('c', chr(1) if part else chr(0))

            section = struct.pack('c', chr(len(section)+2)) + section
            section += struct.pack('c', '\xFF')

            msg_buf += section

        if self.ser_port != None:
            self.ser_port.write(msg_buf)
        #print [ord(x) for x in msg_buf]

    def setPixel(self, x, y, color):

        message = SerialMessage(CommandType.SETPIXEL, [x, y, color])
        self._send_message(message)

    def putText(self, color, x, y, text, font, clear=False):

        message = SerialMessage(CommandType.TEXT, [x, y, color, text, font, clear])
        self._send_message(message)

    def fill(self, color):

        message = SerialMessage(CommandType.FILL, [color])
        self._send_message(message)

    def clear(self):

        message = SerialMessage(CommandType.CLEAR, [])
        self._send_message(message)

    def begin_screen(self):

        message = SerialMessage(CommandType.BEGIN, [])
        self._send_message(message)

    def end_screen(self):

        message = SerialMessage(CommandType.END, [])
        self._send_message(message)
