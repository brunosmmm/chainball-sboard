"""Handle configuration files."""

import os
import json

_DEFAULT_PATH = "/etc/chainball/"

_SCOREBOARD_DEFAULTS = {
    "live_updates": True,
    "chainball_server": "",
    "chainball_server_token": "",
}

_CONFIGURATION_DEFAULTS = {"scoreboard.json": _SCOREBOARD_DEFAULTS}


class ChainBallConfigurationError(Exception):
    """Configuration Error."""


class ChainBallConfigurationFile:
    """Configuration file."""

    def __init__(self, data, defaults=None):
        """Initialize."""

        self._data = data
        if defaults is not None:
            for name, value in defaults.items():
                if name not in self._data:
                    self._data[name] = value

    def __getattr__(self, name):
        """Get attribute."""
        if name in self._data:
            return self._data[name]

        raise AttributeError

    def __getitem__(self, item):
        """Get item."""
        return self._data[item]

    def __contains__(self, item):
        """Contains or not."""
        return self._data.__contains__(item)


class ChainBallConfiguration:
    """Configuration."""

    def __init__(self, extrapaths=None, load_now=False):
        """Initialize."""
        self._config_paths = [_DEFAULT_PATH]
        self._config_files = {}
        if extrapaths is not None:
            if not isinstance(extrapaths, (list, tuple)):
                extrapaths = [extrapaths]

            self._config_paths.extend(extrapaths)

        self._loaded = False
        if load_now:
            try:
                self.load_configuration()
            except ChainBallConfigurationError:
                pass

    def __getattr__(self, name):
        """Get attribute."""
        if name in self._config_files:
            return self._config_files[name]

        raise AttributeError

    @property
    def configuration_loaded(self):
        """Get whether configuration is loaded."""
        return self._loaded

    def load_configuration(self):
        """Try to load configuration."""

        def load_json_file(path):
            with open(path, "r") as fobj:
                return json.load(fobj)

        for path in self._config_paths:
            if not os.path.exists(path):
                continue

            found_files = os.listdir(path)
            for file_name in found_files:
                defaults = _CONFIGURATION_DEFAULTS.get(file_name)
                fname, ext = os.path.splitext(file_name)
                if ext == ".json":
                    try:
                        self._config_files[fname] = ChainBallConfigurationFile(
                            load_json_file(os.path.join(path, file_name)),
                            defaults=defaults,
                        )
                    except (OSError, json.JSONDecodeError):
                        raise ChainBallConfigurationError(
                            "couldnt load configuration file"
                        )
            self._loaded = True
            return

        raise ChainBallConfigurationError("no configuration files available")

    def retrieve_configuration(self, config):
        """Get configuration."""
        configuration = self._config_files.get(config)
        if configuration is None:
            raise ChainBallConfigurationError(
                "configuration entry {} was not found".format(config)
            )

        return configuration


CHAINBALL_CONFIGURATION = ChainBallConfiguration(
    extrapaths=os.path.join(os.getcwd(), "conf"), load_now=True
)
