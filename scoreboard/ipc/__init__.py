"""Chainball game IPC."""

import zmq
import time
from collections import deque
from scoreboard.util.threads import StoppableThread


class ChainballInvalidIPCRequestError(Exception):
    """Invalid IPC request."""


class ChainballIPCRequestMissingFieldError(Exception):
    """IPC request missing required field."""


class ChainballIPCInternalError(Exception):
    """Internal error occurred."""


class ChainballIPCNotAvailableError(Exception):
    """IPC subsystem not available."""


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


class VerifyIPCFields:
    """Verify required fields."""

    def __init__(self, *args):
        """Initialize."""
        self._required_fields = args

    def __call__(self, function):
        """Call."""

        def fn_wrapper(**kwargs):
            for arg in self._required_fields:
                if arg not in kwargs:
                    raise ChainballIPCRequestMissingFieldError(
                        "missing required field {}".format(arg)
                    )
            return function(**kwargs)

        return fn_wrapper


def ipc_ok_response(resp_data):
    """Make OK response."""
    response = ("ok", resp_data)
    return response


def ipc_error_response(resp_data):
    """Make error response."""
    response = ("error", resp_data)
    return response


class ChainballMainIPC(StoppableThread):
    """Main IPC."""

    RESPONSE_ERROR = "error"
    RESPONSE_OK = "ok"

    ERROR_INVALID_REQ = "invalid request"
    ERROR_NOT_SUPPORTED = "request not supported"
    ERROR_INTERNAL = "internal error occurred"
    ERROR_NOT_AVAILABLE = "IPC not available"

    def __init__(self):
        """Initialize."""
        super().__init__()
        self._game = None

    def run(self):
        """Run IPC server."""
        ctx = zmq.Context()
        rep_socket = ctx.socket(zmq.REP)
        rep_socket.bind("tcp://127.0.0.1:5555")
        while not self.is_stopped():
            req_type, req_data = rep_socket.recv_json()

            try:
                response = self._process_request(req_type, req_data)
            except ChainballInvalidIPCRequestError:
                response = (self.RESPONSE_ERROR, self.ERROR_INVALID_REQ)
            except ChainballIPCRequestMissingFieldError as ex:
                response = (self.RESPONSE_ERROR, str(ex))
            except NotImplementedError:
                response = (self.RESPONSE_ERROR, self.ERROR_NOT_SUPPORTED)
            except ChainballIPCInternalError:
                response = (self.RESPONSE_ERROR, self.ERROR_INTERNAL)
            except ChainballIPCNotAvailableError:
                response = (self.RESPONSE_ERROR, self.ERROR_NOT_AVAILABLE)

            rep_socket.send_json(response)

    def associate_game(self, game_obj):
        """Associate game object."""
        self._game = game_obj

    def _process_request(self, req_type, req_data):
        """Process request."""
        if self._game is None:
            raise ChainballIPCNotAvailableError("not available")

        if not hasattr(self, "ipc_{}".format(req_type)):
            raise ChainballInvalidIPCRequestError("invalid request type")

        # call
        ipc_function = getattr(self, "ipc_{}".format(req_type))
        response = ipc_function(self._game, **req_data)
        if response is None:
            response = (self.RESPONSE_OK, None)
        elif isinstance(response, (list, tuple)):
            if len(response) < 2:
                if response[0] == "ok":
                    # whatever
                    response = ("ok", None)
                else:
                    # errors must have an error field
                    raise ChainballIPCInternalError("internal error ocurred")
        else:
            raise ChainballIPCInternalError("internal error occurred")
        return response

    @staticmethod
    def ipc_game_can_start(game, **req_data):
        """Get whether game can start."""
        return ipc_ok_response(game.game_can_start())

    @staticmethod
    def ipc_score_status(game, **req_data):
        """Get score status."""

    @staticmethod
    def ipc_player_status(game, **req_data):
        """Get player status."""

    @staticmethod
    def ipc_tournament_active(game, **req_data):
        """Get tournament status."""

    @staticmethod
    @VerifyIPCFields("tournamentId")
    def ipc_activate_tournament(game, **req_data):
        """Activate tournament."""

    @staticmethod
    def ipc_deactivate_tournament(game, **req_data):
        """Deactivate tournament."""

    @staticmethod
    def ipc_update_registry(game, **req_data):
        """Update local registry."""

    @staticmethod
    @VerifyIPCFields("registryId")
    def ipc_retrieve_registry(game, **req_data):
        """Retrieve local registry."""

    @staticmethod
    def ipc_game_begin(game, **req_data):
        """Start game."""

    @staticmethod
    def ipc_game_end(game, **req_data):
        """End game."""

    @staticmethod
    @VerifyIPCFields("playerNumber")
    def ipc_remote_pair(game, **req_data):
        """Pair remote."""
        raise NotImplementedError

    @staticmethod
    @VerifyIPCFields("playerNumber")
    def ipc_remote_unpair(game, **req_data):
        """Unpair remote."""
        raise NotImplementedError

    @staticmethod
    @VerifyIPCFields("playerNum", "webTxt", "panelTxt")
    def ipc_player_register(game, **req_data):
        """Register player."""

    @staticmethod
    @VerifyIPCFields("playerNumber")
    def ipc_player_unregister(game, **req_data):
        """Unregister player."""

    @staticmethod
    @VerifyIPCFields("playerNum", "evtType")
    def ipc_score_event(game, **req_data):
        """Scoring event."""

    @staticmethod
    @VerifyIPCFields("playerNum")
    def ipc_set_turn(game, **req_data):
        """Set turn."""

    @staticmethod
    @VerifyIPCFields("playerNum", "score")
    def ipc_set_score(game, **req_data):
        """Set score."""


class ChainballIPCHandler:
    """IPC Handler."""

    def __init__(self):
        """Initialize."""
        self._evt_pub = ChainballEventPublisher(5556)
        self._main_ipc = ChainballMainIPC()

    def associate_game(self, game):
        """Associate game."""
        self._main_ipc.associate_game(game)

    def start_handler(self):
        """Start handler."""
        self._evt_pub.start()
        self._main_ipc.start()

    def stop_handler(self):
        """Stop handler."""
        self._evt_pub.stop()
        self._evt_pub.join()
        self._main_ipc.stop()
        self._main_ipc.join()

    def publish_event(self, evt_type, evt_data):
        """Publish event."""
        self._evt_pub.publish(evt_type, evt_data)


IPC_HANDLER = ChainballIPCHandler()
