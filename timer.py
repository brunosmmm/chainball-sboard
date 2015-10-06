from matrixser import MatrixControllerSerial, Color
import signal, os
import datetime
#import subprocess32
import time
import logging
from collections import deque

class TimerAnnouncement(object):
    def __init__(self, heading, text, callback=None, cb_args=None):
        self.heading = heading
        self.text = text
        self.cb = callback
        self.cb_args = cb_args

class TimerHandler(object):

    def __init__(self, timer_end=None):

        self.logger = logging.getLogger('sboard.timer')
        #self.logger.debug('Spawning matrix control server')
        #summon matrix server?
        #self.matSrv = subprocess32.Popen('./matrixsrv/matrixsrv')
        #time.sleep(1)

        self.matCli = MatrixControllerSerial('/dev/ttyUSB0')
        self.matCli.clear()

        #CONVERT INTO STATE MACHINE!!!
        self.stopped = True
        self.paused = False
        self.announcing = False
        self.powered_off = False
        #END STATES
        self.a_msg = None
        self.a_duration = None
        self.a_start = None
        self.pause_timer = None
        self.timer_end = None
        self.end_cb = timer_end

        #shit
        self.last_cycle = datetime.datetime.now()

        #announcement queue
        self.a_queue = deque()

    def setup(self, minutes, seconds=0):
        self.draw(minutes, seconds)

    def start(self, minutes):
        now = datetime.datetime.now()
        self.last_cycle = now
        self.timer_end = now + datetime.timedelta(minutes=minutes)
        self.stopped = False

    def pause(self):
        self.paused = True
        #signal.alarm(0)

        self.pause_timer = self.timer_end - datetime.datetime.now()

    def unpause(self):
        
        self.timer_end = datetime.datetime.now() + self.pause_timer
        self.pause_timer = None

        self.paused = False
        #signal.alarm(1)

    def stop(self, clear=False):
        self.stopped = True
        #signal.alarm(0)

        if clear:
            self.matCli.clear()

    def handle(self):

        td = datetime.datetime.now() - self.last_cycle
        if td.seconds < 1:
            return

        #self.logger.debug('Refreshing matrix')
        self.last_cycle = datetime.datetime.now()

        if self.announcing:
            self.logger.debug('announcing')
            self.draw_announcement()
            td = datetime.datetime.now() - self.a_start
            if td.seconds >= self.a_duration:
                self.logger.debug('Announcement ends: delta = {}, duration = {}'.format(td.seconds, self.a_duration))
                self.announcing = False
                self.a_start = None
                if self.a_msg.cb != None:
                    if self.a_msg.cb_args:
                        self.a_msg.cb(self.a_msg.cb_args)
                    else:
                        self.a_msg.cb()
                self.a_msg = None
            return
        else:
            if len(self.a_queue) > 0:
                #hack hack hack hack
                #self.logger.debug('popping announcement, len(queue) = {}'.format(len(self.a_queue)))
                self._announcement(*self.a_queue.popleft())


        if self.stopped or self.powered_off or self.paused:
            return

        self.refresh_matrix()

        diff = self.timer_end - datetime.datetime.now()
        if diff.seconds == 0:
            self.stopped = True
            self.refresh_matrix()
            if self.end_cb:
                self.end_cb()
                return

        #signal.alarm(1)

    def draw(self, minutes, seconds):

        if minutes > 9:
            m_r = int(0.425*(1200 - (minutes*60 + seconds)))
            m_g = 255
        else:
            m_r = 255
            m_g = int(0.425*(minutes*60 + seconds))

        min_str = "{:0>2d}".format(minutes)
        sec_str = "{:0>2d}".format(seconds)

        #quick hack, no time to dig in deeper
        if m_r > 255:
            m_r = 255
        if m_g > 255:
            m_g = 255

        if m_r < 0:
            m_r = 0
        if m_g < 0:
            m_g = 0


        self.matCli.putText(Color(m_r,m_g,0), 0, 1, min_str[0], 2, clear=True)
        self.matCli.putText(Color(m_r,m_g,0), 11, 1, min_str[1], 2)
        #self.matCli.putText(Color(255,0,0), 16, 0, ':', 2)
        self.matCli.putText(Color(255,0,0), 21, 0, sec_str, 1)
        self.matCli.end_screen()

    def draw_announcement(self):

        self.matCli.begin_screen()

        xoff = 1
        text = '{:^6}'.format(self.a_msg.heading)
        for c in text:
            self.matCli.putText(Color(255, 255, 255), xoff, 0, c, 1)
            xoff += 5

        if len(self.a_msg.text) > 0:
            xoff = 1
            #format
            text = '{:^6}'.format(self.a_msg.text)
            for c in text:
                self.matCli.putText(Color(0, 255, 255), xoff, 8, c, 1)
                xoff += 5

        self.matCli.end_screen()

    def poweroff_matrix(self):
        self.matCli.begin_screen()
        self.matCli.end_screen()
        self.powered_off = True

    def poweron_matrix(self):
        self.powered_off = False

    def refresh_matrix(self):

        timer = self.timer_end - datetime.datetime.now()

        #wtf
        if timer.days < 0:
            minutes = 0
            seconds = 0
        else:
            hours, remainder = divmod(timer.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

        self.draw(minutes, seconds)

    #hack hack hack hack
    def announcement(self, announcement, duration):
        self.logger.debug('queuing announcement')
        self.a_queue.append([announcement, duration])

    def _announcement(self, announcement, duration):

        self.logger.debug('Announcing: {} -> {}'.format(announcement.heading, announcement.text))

        self.a_msg = announcement
        self.a_duration = duration
        self.a_start = datetime.datetime.now()
        self.announcing = True
