"""Handle configuration files."""

import os
import json

_DEFAULT_PATH = "/etc/chainball/"


class ChainBallConfigurationError(Exception):
    """Configuration Error."""


class ChainBallConfiguration:
    """Configuration."""

    def __init__(self, extrapaths=None):
        """Initialize."""
        self._config_paths = [_DEFAULT_PATH]
        self._config_files = {}
        if extrapaths is not None:
            if not isinstance(extrapaths, (list, tuple)):
                extrapaths = [extrapaths]

            self._config_paths.extend(extrapaths)

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
                fname, ext = os.path.splitext(file_name)
                if ext == ".json":
                    try:
                        self._config_files[fname] = load_json_file(
                            os.path.join(path, file_name)
                        )
                    except (OSError, json.JSONDecodeError):
                        raise ChainBallConfigurationError(
                            "couldnt load configuration file"
                        )
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
