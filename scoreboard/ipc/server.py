"""Main IPC server."""

import zmq

from scoreboard.cbcentral.localdb import (
    GAME_REGISTRY,
    PLAYER_REGISTRY,
    TOURNAMENT_REGISTRY,
    update_all,
)
from scoreboard.game.exceptions import (
    NotEnoughPlayersError,
    PlayerNotPairedError,
    PlayerNotRegisteredError,
    PlayerRemoteNotPaired,
    TooManyPlayersError,
    ChainballGameError,
)
from scoreboard.game.playertxt import PlayerText
from scoreboard.ipc import (
    ChainballInvalidIPCRequestError,
    ChainballIPCInternalError,
    ChainballIPCNotAvailableError,
    ChainballIPCRequestFieldTypeError,
    ChainballIPCRequestMissingFieldError,
    VerifyIPCFields,
    fail_game_live,
    fail_game_stopped,
    ipc_error_response,
    ipc_ok_response,
)
from scoreboard.ipc.publisher import ChainballEventPublisher
from scoreboard.util.threads import StoppableThread

DEBUG = True


class ChainballMainIPC(StoppableThread):
    """Main IPC."""

    RESPONSE_ERROR = "error"
    RESPONSE_OK = "ok"

    ERROR_INVALID_REQ = "invalid request"
    ERROR_NOT_SUPPORTED = "request not supported"
    ERROR_INTERNAL = "internal error occurred"
    ERROR_WRONG_TYPE = "wrong data type"
    ERROR_NOT_AVAILABLE = "IPC not available"

    def __init__(self, port=5555):
        """Initialize."""
        super().__init__()
        self._game = None
        self._port = port

    def run(self):
        """Run IPC server."""
        ctx = zmq.Context()
        rep_socket = ctx.socket(zmq.REP)
        rep_socket.setsockopt(zmq.RCVTIMEO, 1000)
        rep_socket.setsockopt(zmq.LINGER, 0)
        rep_socket.bind("tcp://127.0.0.1:{}".format(self._port))
        while not self.is_stopped():
            try:
                req_type, req_data = rep_socket.recv_json()
            except zmq.error.Again:
                # timeout
                continue

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
            except ChainballIPCRequestFieldTypeError:
                response = (self.RESPONSE_ERROR, self.ERROR_WRONG_TYPE)
            except Exception:
                if DEBUG:
                    raise
                response = (self.RESPONSE_ERROR, self.ERROR_INTERNAL)

            rep_socket.send_json(response)

        # cleanup
        rep_socket.close()

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
    def _get_scores(game):
        """Get scores."""
        scores = {
            str(pid): player.current_score
            for pid, player in game.players.items()
        }
        return scores

    @staticmethod
    @fail_game_live
    def ipc_score_status(game, **req_data):
        """Get score status."""
        return ipc_ok_response(ChainballMainIPC._get_scores(game))

    @staticmethod
    def make_player_status(game):
        """Get player status."""
        players = {}
        for player_id, player in game.players.items():
            player_dict = {
                "panel_txt": player.panel_text,
                "web_txt": player.web_text,
                "remote_id": player.remote_id,
                "username": player.registry_username,
                "registered": player.registered,
            }
            players[str(player_id)] = player_dict
        return players

    @staticmethod
    def ipc_player_status(game, **req_data):
        """Get player status."""
        players = ChainballMainIPC.make_player_status(game)
        return ipc_ok_response(players)

    @staticmethod
    def ipc_game_status(game, **req_data):
        """Get game status."""
        if game.ongoing:
            if game.paused:
                status_string = "paused"
            else:
                status_string = "started"
        elif game.finished:
            status_string = "finished"
        else:
            status_string = "stopped"

        if game.tournament_mode:
            tournament = TOURNAMENT_REGISTRY[game.tournament_id]
            tournament_str = "{} {} ".format(
                tournament.season, tournament.description
            )
            if game.active_game_id is not None:
                game_entry = GAME_REGISTRY[game.active_game_id]
                game_seq = game_entry.sequence
            else:
                game_seq = None
        else:
            tournament_str = ""
            game_seq = None
        status = {
            "game": status_string,
            "serving": game.active_player,
            "serving_user_id": game.active_player_id,
            "internal_game_id": game.g_persist.current_game_series,
            "internal_user_id": game.g_persist.get_current_user_id(),
            "scores": ChainballMainIPC._get_scores(game),
            "tournament": game.tournament_mode,
            "tournament_id": game.tournament_id,
            "tournament_str": tournament_str,
            "game_id": game.active_game_id,
            "game_seq": game_seq,
            "players": ChainballMainIPC.make_player_status(game),
            "remaining_time": game.get_remaining_time(),
        }
        return ipc_ok_response(status)

    @staticmethod
    def ipc_tournament_active(game, **req_data):
        """Get tournament status."""
        return ipc_ok_response(game.tournament_id)

    @staticmethod
    @fail_game_live
    @VerifyIPCFields(tournament_id=None)
    def ipc_activate_tournament(game, **req_data):
        """Activate tournament."""
        try:
            tournament_id = int(req_data["tournament_id"])
        except ValueError:
            return ipc_error_response("invalid value")

        if tournament_id not in TOURNAMENT_REGISTRY:
            return ipc_error_response("invalid tournament id")

        try:
            game.activate_tournament(tournament_id)
        except ChainballGameError:
            return ipc_error_response("cannot activate")
        return None

    @staticmethod
    @fail_game_live
    def ipc_deactivate_tournament(game, **req_data):
        """Deactivate tournament."""
        game.deactivate_tournament()

    @staticmethod
    @fail_game_live
    @VerifyIPCFields(game_id=int)
    def ipc_activate_game(game, **req_data):
        """Activate game."""
        try:
            game_id = int(req_data["game_id"])
        except ValueError:
            return ipc_error_response("invalid value")

        if game_id not in GAME_REGISTRY:
            return ipc_error_response("invalid game id")

        try:
            game.set_active_game(game_id)
        except ChainballGameError:
            return ipc_error_response("cannot activate")
        return None

    @staticmethod
    @fail_game_live
    def ipc_update_registry(game, **req_data):
        """Update local registry."""
        update_all()

    @staticmethod
    @VerifyIPCFields(registry_id=str)
    def ipc_retrieve_registry(game, **req_data):
        """Retrieve local registry."""
        registry = req_data["registry_id"]
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
    @VerifyIPCFields(player_number=None)
    def ipc_remote_pair(game, **req_data):
        """Pair remote."""
        raise NotImplementedError

    @staticmethod
    @VerifyIPCFields(player_number=None)
    def ipc_remote_unpair(game, **req_data):
        """Unpair remote."""
        raise NotImplementedError

    @staticmethod
    @fail_game_live
    @VerifyIPCFields(web_txt=str, panel_txt=str)
    def ipc_player_register(game, **req_data):
        """Register player."""
        player_num = req_data.get("player_num")
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
                player_num: PlayerText(
                    req_data["panel_txt"], req_data["web_txt"]
                )
            }
        else:
            player_entry = {
                player_num: PlayerText(
                    registry_data.display_name, registry_data.name
                )
            }
        try:
            game.register_players(player_entry, username)
        except TooManyPlayersError:
            return ipc_error_response("too many players")

        return None

    @staticmethod
    @fail_game_live
    @VerifyIPCFields(player_number=None)
    def ipc_player_unregister(game, **req_data):
        """Unregister player."""
        try:
            game.unregister_players([int(req_data["player_number"])])
        except PlayerNotRegisteredError:
            return ipc_error_response("player not registered")

        return None

    @staticmethod
    @fail_game_stopped
    @VerifyIPCFields("evt_type", player_num=int)
    def ipc_score_event(game, **req_data):
        """Scoring event."""
        game.scoring_evt(req_data["player_num"], req_data["evt_type"])

    @staticmethod
    @fail_game_stopped
    @VerifyIPCFields(player_num=int)
    def ipc_set_turn(game, **req_data):
        """Set turn."""
        game.game_set_active_player(req_data["player_num"])

    @staticmethod
    @VerifyIPCFields(player_num=int, score=int)
    def ipc_set_score(game, **req_data):
        """Set score."""
        game.game_force_score(req_data["player_num"], req_data["score"])


class ChainballIPCHandler:
    """IPC Handler."""

    def __init__(self, server_port=5555, evt_port=5556):
        """Initialize."""
        self._evt_pub = ChainballEventPublisher(evt_port)
        self._main_ipc = ChainballMainIPC(server_port)
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
