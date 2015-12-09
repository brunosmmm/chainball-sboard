import time
from threadutil import StoppableThread
import Queue
import remote.nrf24const as rf
import logging

#constants
CE_PIN_GPIO = 1
HW_COMM_SLEEP = 0.0001
NRF_PAYLOAD_SIZE = 32

#delay hw transactions
def _hw_comm_delay(func):

    time.sleep(HW_COMM_SLEEP)
    return func

class NRF24Chip(object):

    def __init__(self, bus, select, message_cb=None, fake_hw=False):

        self.logger = logging.getLogger('sboard.nrf24')
        self.fake_hw = fake_hw

        if fake_hw == False:
            import RPi.GPIO as gpio
            import spidev

            self.gpio = gpio
            self.spi_dev = spidev.SpiDev()

            try:
                self.spi_dev.open(bus, select)
                self.spi_dev.max_speed_hz = 2000000
                self.logger.debug('CS active HIGH = {}'.format(self.spi_dev.cshigh))
                self.logger.debug('Speed = {}'.format(self.spi_dev.max_speed_hz))
            except IOError:
                self.logger.error('Cant open SPI device')
                raise

            #setup CE pin
            self.gpio.setmode(self.gpio.BCM)
            self.gpio.setup(CE_PIN_GPIO, self.gpio.OUT)
            self.gpio.output(CE_PIN_GPIO, False)

        self.pay_size = NRF_PAYLOAD_SIZE
        self.msg_cb = message_cb

    def set_ce(self):
        self.gpio.output(CE_PIN_GPIO, True)

    def clr_ce(self):
        self.gpio.output(CE_PIN_GPIO, False)

    @_hw_comm_delay
    def write_reg(self, reg_num, reg_data):
        ret = self.spi_dev.xfer2([(rf.CMD_W_REG | reg_num) & 0xFF, reg_data])
        return ret[0]

    @_hw_comm_delay
    def read_reg(self, reg_num):
        ret = self.spi_dev.xfer2([(rf.CMD_R_REG | reg_num) & 0xFF, 0x00])
        return ret[1]

    @_hw_comm_delay
    def readwrite_buffer(self, data):
        return self.spi_dev.xfer2(data)

    def write_buffer(self, data):
        return self.readwrite_buffer(data)

    @_hw_comm_delay
    def read_regdata(self, reg_num, read_size):
        dummy_write = [(rf.CMD_R_REG | reg_num) & 0xFF] + [0x00 for x in range(read_size)]
        return self.spi_dev.xfer2(dummy_write)

    @_hw_comm_delay
    def write_regdata(self, reg_num, data):
        self.spi_dev.xfer2([(rf.CMD_W_REG | reg_num) & 0xFF] + data)

    @_hw_comm_delay
    def writeread(self, value):
        return self.spi_dev.xfer2([value])

    def write(self, value):
        self.writeread(value)

    def get_status(self):
        return self.writeread(rf.CMD_NOP)[0]

    def reset_irq(self, flags):
        self.write_reg(rf.REG_STATUS, flags)

    def tx_payload(self, payload):
        self.write(rf.CMD_FLSH_TX)
        self.write_regdata(rf.CMD_W_PAY, payload)
        self.set_ce()
        time.sleep(0.00015)
        self.clr_ce()

    def rx_payload(self):
        return self.read_regdata(rf.CMD_R_PAY, self.pay_size)

    def tx_powerup(self):
        self.write_reg(rf.REG_CONFIG, rf.EN_CRC|rf.CRCO|rf.PWR_UP|rf.PRIM_TX)

    def rx_powerup(self):
        self.write_reg(rf.REG_CONFIG, rf.EN_CRC|rf.CRCO|rf.PWR_UP|rf.PRIM_RX)

    def initialize(self, addr, channel):

        if self.fake_hw:
            return

        self.logger.debug('initializing with parameters: addr = {}; channel = {}'.format(addr,
                                                                                         channel))
        self.clr_ce()

        self.write_reg(rf.REG_RF_SETUP, rf.RF_SETUP_RF_PWR_6|rf.RF_SETUP_RF_DR_250)
        self.write_reg(rf.REG_RX_PW_P0, NRF_PAYLOAD_SIZE)
        self.write_reg(rf.REG_RF_CH, channel)

        self.write_regdata(rf.REG_RX_ADDR_P0, addr)
        self.write_regdata(rf.REG_TX_ADDR, addr)

        #quick sanity check!
        read_back = self.read_regdata(rf.REG_RX_ADDR_P0, 5)
        self.logger.debug('reading address back: {}'.format(read_back[1:]))
        if cmp(read_back[1:], addr):
            self.logger.debug('communication not reliable')

        self.write_reg(rf.REG_EN_RXADDR, rf.EN_RXADDR_ERX_P0)

        self.reset_irq(rf.STATUS_RX_DR|rf.STATUS_TX_DS|rf.STATUS_MAX_RT)
        #RX MODE
        self.rx_powerup()
        self.set_ce()

    def poll(self):

        if self.fake_hw:
            return

        status = self.get_status()

        if status & rf.STATUS_RX_DR:
            #receive payload
            payload = self.rx_payload()
            self.logger.debug('incoming transmission, len = {}'.format(len(payload)-1))
            #callback
            if self.msg_cb:
                self.msg_cb(payload[1:])

            self.reset_irq(rf.STATUS_RX_DR|rf.STATUS_TX_DS|rf.STATUS_MAX_RT)

        if status & rf.STATUS_TX_DS:
            self.reset_irq(rf.STATUS_TX_DS)
        if status & rf.STATUS_MAX_RT:
            self.reset_irq(rf.STATUS_MAX_RT)

        #check if there are packets in fifo
        while self.read_reg(rf.REG_FIFO_STATUS) & 0x01 == 0:
            #receive payload
            payload = self.rx_payload()
            self.logger.debug('incoming payload from FIFO, len = {}'.format(len(payload)-1))

            if self.msg_cb:
                self.msg_cb(payload[1:])

class NRF24Message(object):

    def __init__(self, payload):

        self.payload = payload
        self.timestamp = time.time()

class NRF24Handler(StoppableThread):

    ADDRESS = [0x11, 0x22, 0x33, 0x44, 0x55]
    CHANNEL = 2

    def __init__(self, fake_hw=False):
        super(NRF24Handler, self).__init__()

        #logging
        self.logger = logging.getLogger('sboard.remote')

        #create SPI device
        self.chip = NRF24Chip(0, 0, self._message_callback, fake_hw=fake_hw)

        #initialize HW
        self.initialize_hardware()

        #message queue
        self.msg_q = Queue.Queue()

    def initialize_hardware(self):
        #initialize HW
        self.logger.debug('Initializing NRF24 HW')
        self.chip.initialize(self.ADDRESS, self.CHANNEL)

    def _message_callback(self, payload):
        #process payload
        try:
            self.logger.debug('Received payload, length is {}'.format(len(payload)))
            #self.logger.debug('payload dump: {}'.format([hex(x) for x in payload]))
        except TypeError:
            self.logger.debug('Payload is wrong type, dump: {}'.format(payload))
        self.msg_q.put(NRF24Message(payload))

    def message_pending(self):
        return not self.msg_q.empty()

    def receive_message(self):
        return self.msg_q.get()

    def run(self):

        #poll continuously to detect reception
        while True:

            if self.is_stopped():
                #quit
                exit(0)

            #execute low-level cycle
            self.chip.poll()

            #throttle cycle
            time.sleep(0.01)
