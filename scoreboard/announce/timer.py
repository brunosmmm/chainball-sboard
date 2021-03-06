"""Game timer controller."""

import datetime
import logging
from collections import deque

from scoreboard.announce.matrixser import Color, MatrixControllerSerial


class AnnouncementKind:
    """Announcement types."""

    PLAYER_PANEL = 0
    TIMER_PANEL = 1


class TimerAnnouncement:
    """Timer panel announcement."""

    def __init__(self, heading, text, callback=None, cb_args=None):
        """Initialize."""
        self.heading = heading
        self.text = text
        self.cb = callback
        self.cb_args = cb_args


class TimerHandler:
    """Timer panel controller."""

    def __init__(self, timer_end=None, chainball_game=None, rgbmat=True):
        """Initialize."""
        if rgbmat:
            self.logger = logging.getLogger("sboard.timer")
        else:
            self.logger = logging.getLogger("sboard.ptimer")

        if rgbmat:
            self.matCli = MatrixControllerSerial("/dev/ttyUSB0")
            self.matCli.clear()
        else:
            self.matCli = None

        self.stopped = True
        self.paused = False
        self.announcing = False
        self.powered_off = False
        # END STATES
        self.a_msg = None
        self.a_duration = None
        self.a_start = None
        self.pause_timer = None
        self.timer_end = None
        self.end_cb = timer_end
        self.a_kind = None
        self.a_player = None

        # game reference
        # NEEDS DECOUPLING
        self.game = chainball_game

        self.last_cycle = datetime.datetime.now()

        # announcement queue
        self.a_queue = deque()

    def setup(self, minutes, seconds=0):
        """Set default state."""
        self.draw(minutes, seconds)

    def start(self, minutes):
        """Start timer."""
        now = datetime.datetime.now()
        self.last_cycle = now
        self.timer_end = now + datetime.timedelta(minutes=minutes)
        self.stopped = False

    def pause(self):
        """Pause timer."""
        self.paused = True

        self.pause_timer = self.timer_end - datetime.datetime.now()

    def unpause(self):
        """Unpause timer."""
        self.timer_end = datetime.datetime.now() + self.pause_timer
        self.pause_timer = None

        self.paused = False

    def stop(self, clear=False):
        """Stop timer."""
        self.stopped = True
        if clear:
            if self.matCli:
                self.matCli.clear()

    def get_timer(self):
        """Get current timer value."""
        if self.timer_end is None or self.stopped:
            return None

        if self.paused:
            return self.pause_timer

        return self.timer_end - datetime.datetime.now()

    def handle(self):
        """Do main timer logic."""
        td = datetime.datetime.now() - self.last_cycle
        if td.seconds < 1:
            return

        self.last_cycle = datetime.datetime.now()

        if self.announcing:
            if self.a_kind == AnnouncementKind.TIMER_PANEL:
                self.draw_announcement()
            elif self.a_kind == AnnouncementKind.PLAYER_PANEL:
                self.game.players[self.a_player].show_text(self.a_msg.text)
            td = datetime.datetime.now() - self.a_start
            if td.seconds >= self.a_duration:
                self.logger.debug(
                    "Announcement ends: delta = {},"
                    " duration = {}".format(td.seconds, self.a_duration)
                )

                if self.a_kind == AnnouncementKind.PLAYER_PANEL:
                    # restore player text
                    self.game.players[self.a_player].restore_text()

                self.announcing = False
                self.a_start = None
                self.a_player = None
                self.a_kind = None
                if self.a_msg.cb is not None:
                    if self.a_msg.cb_args:
                        self.a_msg.cb(self.a_msg.cb_args)
                    else:
                        self.a_msg.cb()
                self.a_msg = None
            return
        else:
            if len(self.a_queue) > 0:
                # hack hack hack hack
                self._announcement(*self.a_queue.popleft())

        if self.stopped or self.powered_off or self.paused:
            return

        if self.matCli:
            self.refresh_matrix()

        diff = self.timer_end - datetime.datetime.now()
        if diff.seconds == 0:
            self.stopped = True
            self.refresh_matrix()
            if self.end_cb:
                self.end_cb()
                return

    def draw(self, minutes, seconds):
        """Draw timer text."""
        if minutes > 9:
            m_r = int(0.425 * (1200 - (minutes * 60 + seconds)))
            m_g = 255
        else:
            m_r = 255
            m_g = int(0.425 * (minutes * 60 + seconds))

        min_str = "{:0>2d}".format(minutes)
        sec_str = "{:0>2d}".format(seconds)

        # quick hack, no time to dig in deeper
        if m_r > 255:
            m_r = 255
        if m_g > 255:
            m_g = 255

        if m_r < 0:
            m_r = 0
        if m_g < 0:
            m_g = 0

        self.matCli.putText(Color(m_r, m_g, 0), 0, 1, min_str[0], 2, clear=True)
        self.matCli.putText(Color(m_r, m_g, 0), 11, 1, min_str[1], 2)
        self.matCli.putText(Color(255, 0, 0), 21, 0, sec_str, 1)
        self.matCli.end_screen()

    def draw_announcement(self):
        """Draw announcement."""
        self.matCli.begin_screen()

        xoff = 1
        text = "{:^6}".format(self.a_msg.heading)
        for c in text:
            self.matCli.putText(Color(255, 255, 255), xoff, 0, c, 1)
            xoff += 5

        if len(self.a_msg.text) > 0:
            xoff = 1
            # format
            text = "{:^6}".format(self.a_msg.text)
            for c in text:
                self.matCli.putText(Color(0, 255, 255), xoff, 8, c, 1)
                xoff += 5

        self.matCli.end_screen()

    def poweroff_matrix(self):
        """Turn matrix off."""
        self.matCli.begin_screen()
        self.matCli.end_screen()
        self.powered_off = True

    def poweron_matrix(self):
        """Turn matrix on."""
        self.powered_off = False

    def get_remaining_time(self):
        """Get remaining time."""
        timer = self.timer_end - datetime.datetime.now()

        if timer.days < 0:
            minutes = 0
            seconds = 0
        else:
            hours, remainder = divmod(timer.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

        return (minutes, seconds)

    def refresh_matrix(self):
        """Refresh matrix."""
        self.draw(*self.get_remaining_time())

    # hack hack hack hack
    def announcement(self, announcement, duration):
        """Do announcement."""
        self.logger.debug("queuing announcement")
        self.a_queue.append([announcement, duration, -1])

    def player_announcement(self, announcement, duration, player_number):
        """Do announcement on player panels."""
        self.logger.debug("queuing player announcement")
        self.a_queue.append([announcement, duration, player_number])

    def _announcement(self, announcement, duration, player_panel):

        self.logger.debug(
            "Announcing: {} -> {}".format(
                announcement.heading, announcement.text
            )
        )

        if player_panel > -1:
            self.a_kind = AnnouncementKind.PLAYER_PANEL
            self.a_player = player_panel
        else:
            self.a_kind = AnnouncementKind.TIMER_PANEL

        self.a_msg = announcement
        self.a_duration = duration
        self.a_start = datetime.datetime.now()
        self.announcing = True
