"""Utility threads."""

import threading
import uuid


class StoppableThread(threading.Thread):
    """Stoppable thread."""

    def __init__(self):
        """Initialize."""
        super(StoppableThread, self).__init__()
        self.stop_flag = threading.Event()

    def stop(self):
        """Stop thread."""
        self.stop_flag.set()

    def is_stopped(self):
        """Get if running or stopped."""
        return self.stop_flag.isSet()


class CallbackStoppableThread(StoppableThread):
    """Stoppable thread with callback on stop."""

    def __init__(self, callback):
        """Initialize."""
        super(CallbackStoppableThread, self).__init__()
        self.callback = callback
        self.uuid = uuid.uuid1()

    def stop(self):
        """Stop thread."""
        super(CallbackStoppableThread, self).stop()
        if self.callback:
            self.callback(self.uuid)
