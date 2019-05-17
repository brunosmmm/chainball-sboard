"""Chainball game IPC."""


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
