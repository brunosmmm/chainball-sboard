"""Event publisher."""

import time
import zmq

from collections import deque

from scoreboard.util.threads import StoppableThread


class ChainballEventPublisher(StoppableThread):
    """Event publisher."""

    def __init__(self, port):
        """Initialize."""
        super().__init__()
        self._port = port
        self._queue = deque()

    def publish(self, evt_type, evt_data):
        """Publish event."""
        event = (evt_type, evt_data)
        self._queue.append(event)

    def run(self):
        """Run publisher."""
        ctx = zmq.Context()
        pub_socket = ctx.socket(zmq.PUB)
        pub_socket.bind("tcp://127.0.0.1:{}".format(self._port))

        while not self.is_stopped():
            try:
                evt_type, evt_data = self._queue.popleft()
            except IndexError:
                continue

            pub_socket.send_json((evt_type, evt_data))

            time.sleep(0.1)

        pub_socket.close()
