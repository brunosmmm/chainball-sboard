"""Chainball game IPC."""

import zmq
import time
from collections import deque
from scoreboard.util.threads import StoppableThread
from scoreboard.game.exceptions import (
    NotEnoughPlayersError,
    PlayerNotPairedError,
    PlayerRemoteNotPaired,
    TooManyPlayersError,
    PlayerNotRegisteredError,
)
from scoreboard.game.playertxt import PlayerText
from scoreboard.cbcentral.localdb import (
    PLAYER_REGISTRY,
    TOURNAMENT_REGISTRY,
    GAME_REGISTRY,
    update_all,
)


class ChainballInvalidIPCRequestError(Exception):
    """Invalid IPC request."""


class ChainballIPCRequestMissingFieldError(Exception):
    """IPC request missing required field."""


class ChainballIPCInternalError(Exception):
    """Internal error occurred."""


class ChainballIPCNotAvailableError(Exception):
    """IPC subsystem not available."""


class ChainballIPCRequestFieldTypeError(Exception):
    """Wrong field type."""


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

    def __init__(self, *args, **kwargs):
        """Initialize."""
        self._required_fields = kwargs
        for arg in args:
            self._required_fields[arg] = None

    def __call__(self, function):
        """Call."""

        def fn_wrapper(*args, **kwargs):
            for arg, arg_type in self._required_fields.items():
                if arg not in kwargs:
                    raise ChainballIPCRequestMissingFieldError(
                        "missing required field {}".format(arg)
                    )
                if arg_type is None:
                    continue
                # check type
                if not isinstance(kwargs[arg], arg_type):
                    raise ChainballIPCRequestFieldTypeError(
                        "field {} has wrong type, expected {}".format(
                            arg, arg_type
                        )
                    )
            return function(*args, **kwargs)

        return fn_wrapper


def ipc_ok_response(resp_data):
    """Make OK response."""
    response = ("ok", resp_data)
    return response


def ipc_error_response(resp_data):
    """Make error response."""
    response = ("error", resp_data)
    return response


def fail_game_live(function):
    """Fail if game live decorator."""

    def fn_wrapper(game, **kwargs):
        if game.ongoing:
            return ipc_error_response("game is live")
        return function(game, **kwargs)

    return fn_wrapper


def fail_game_stopped(function):
    """Fail if game stopped decorator."""

    def fn_wrapper(game, **kwargs):
        if not game.ongoing:
            return ipc_error_response("game is stopped")
        return function(game, **kwargs)

    return fn_wrapper


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
            except Exception:
                response = (self.RESPONSE_ERROR, self.ERROR_INTERNAL)

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
        if req_data is None:
            req_data = {}
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
    @fail_game_live
    def ipc_score_status(game, **req_data):
        """Get score status."""
        scores = {
            str(pid): player.current_score
            for pid, player in game.players.items()
        }
        return ipc_ok_response(scores)

    @staticmethod
    def ipc_player_status(game, **req_data):
        """Get player status."""
        players = {}
        for player_id, player in game.players.items():
            player_dict = {
                "panelTxt": player.panel_text,
                "webTxt": player.web_text,
                "remoteId": player.remote_id,
                "username": player.registry_username,
            }
            players[str(player_id)] = player_dict
        return ipc_ok_response(players)

    @staticmethod
    def ipc_tournament_active(game, **req_data):
        """Get tournament status."""
        return ipc_ok_response(game.tournament_id)

    @staticmethod
    @fail_game_live
    @VerifyIPCFields(tournamentId=None)
    def ipc_activate_tournament(game, **req_data):
        """Activate tournament."""
        try:
            tournament_id = int(req_data["tournamentId"])
        except ValueError:
            return ipc_error_response("invalid value")

        if tournament_id not in TOURNAMENT_REGISTRY:
            return ipc_error_response("invalid tournament id")

        game.activate_tournament(tournament_id)
        return None

    @staticmethod
    @fail_game_live
    def ipc_deactivate_tournament(game, **req_data):
        """Deactivate tournament."""
        game.deactivate_tournament()

    @staticmethod
    @fail_game_live
    def ipc_update_registry(game, **req_data):
        """Update local registry."""
        update_all()

    @staticmethod
    @VerifyIPCFields(registryId=str)
    def ipc_retrieve_registry(game, **req_data):
        """Retrieve local registry."""
        registry = req_data["registryId"]
        if registry == "player":
            return ipc_ok_response(PLAYER_REGISTRY.serialized)
        if registry == "tournament":
            return ipc_ok_response(TOURNAMENT_REGISTRY.serialized)
        if registry == "game":
            return ipc_ok_response(GAME_REGISTRY.serialized)
        return ipc_error_response("invalid registry")

    @staticmethod
    @fail_game_live
    def ipc_game_begin(game, **req_data):
        """Start game."""
        try:
            game.game_begin()
        except NotEnoughPlayersError:
            return ipc_error_response("at least 2 players needed")
        except PlayerNotPairedError:
            return ipc_error_response("player not paired")
        except PlayerRemoteNotPaired:
            return ipc_error_response("player remote not paired")

        return None

    @staticmethod
    @fail_game_stopped
    def ipc_game_end(game, **req_data):
        """End game."""
        game.game_end(reason="FORCED_STOP")

    @staticmethod
    @VerifyIPCFields(playerNumber=None)
    def ipc_remote_pair(game, **req_data):
        """Pair remote."""
        raise NotImplementedError

    @staticmethod
    @VerifyIPCFields(playerNumber=None)
    def ipc_remote_unpair(game, **req_data):
        """Unpair remote."""
        raise NotImplementedError

    @staticmethod
    @fail_game_live
    @VerifyIPCFields(webTxt=str, panelTxt=str)
    def ipc_player_register(game, **req_data):
        """Register player."""
        player_num = req_data.get("playerNum")
        if player_num is None:
            game.next_player_num()

        username = req_data.get("username")
        if username is not None:
            try:
                registry_data = PLAYER_REGISTRY[username]
            except KeyError:
                username = None

        if username is None:
            player_entry = {
                player_num: PlayerText(req_data["panelTxt"], req_data["webTxt"])
            }
        else:
            player_entry = {
                player_num: PlayerText(
                    registry_data.display_name, registry_data.name
                )
            }
        try:
            game.register_players(player_entry)
        except TooManyPlayersError:
            return ipc_error_response("too many players")

        return None

    @staticmethod
    @fail_game_live
    @VerifyIPCFields(playerNumber=None)
    def ipc_player_unregister(game, **req_data):
        """Unregister player."""
        try:
            game.unregister_players([int(req_data["playerNumber"])])
        except PlayerNotRegisteredError:
            return ipc_error_response("player not registered")

        return None

    @staticmethod
    @fail_game_stopped
    @VerifyIPCFields("evtType", playerNum=int)
    def ipc_score_event(game, **req_data):
        """Scoring event."""
        game.scoring_evt(req_data["playerNum"], req_data["evtType"])

    @staticmethod
    @fail_game_stopped
    @VerifyIPCFields(playerNum=int)
    def ipc_set_turn(game, **req_data):
        """Set turn."""
        game.set_active_player(req_data["playerNum"])

    @staticmethod
    @VerifyIPCFields(playerNum=int, score=int)
    def ipc_set_score(game, **req_data):
        """Set score."""
        game.game_force_score(req_data["playerNum"], req_data["score"])


class ChainballIPCHandler:
    """IPC Handler."""

    def __init__(self):
        """Initialize."""
        self._evt_pub = ChainballEventPublisher(5556)
        self._main_ipc = ChainballMainIPC()
        self._running = False

    def associate_game(self, game):
        """Associate game."""
        self._main_ipc.associate_game(game)

    def start_handler(self):
        """Start handler."""
        if self._running:
            return
        self._evt_pub.start()
        self._main_ipc.start()
        self._running = True

    def stop_handler(self):
        """Stop handler."""
        if self._running is False:
            return
        self._evt_pub.stop()
        self._evt_pub.join()
        self._main_ipc.stop()
        self._main_ipc.join()
        self._running = False

    def publish_event(self, evt_type, evt_data):
        """Publish event."""
        if self._running is False:
            raise ChainballIPCNotAvailableError
        self._evt_pub.publish(evt_type, evt_data)


IPC_HANDLER = ChainballIPCHandler()
