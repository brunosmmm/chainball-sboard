"""Map remote buttons to actions."""


from game.constants import GameTurnActions, MasterRemoteActions
import re
import json
import logging


class RemoteMappingLoadFailed(Exception):
    """Mapping failed exception."""

    pass


class RemoteMappingIllegalError(Exception):
    """File has illegal syntax."""

    pass


class RemoteMapping(object):
    """Mapping logic class."""

    # configuration file name mapping
    PLAYER_ACTIONS = {
        "INCR": GameTurnActions.INCREASE_SCORE,
        "DECR": GameTurnActions.DECREASE_SCORE,
        "PASS": GameTurnActions.PASS_TURN,
    }
    MASTER_ACTIONS = {"PAUSE": MasterRemoteActions.PAUSE_UNPAUSE_CLOCK}

    def __init__(self, logger_name):
        """Initialize.

        Args
        ----
        logger: str
            Logger name
        """
        self.logger = logging.getLogger(logger_name)
        self.player_mapping = {}
        self.master_mapping = {}

    def load_config(self, filename):
        """Load mapping configuration.

        Args
        ----
        filename: str
           File path for configuration
        """
        try:
            remote_map_file = open(filename)
            remote_map = json.load(remote_map_file)
            remote_map_file.close()
        except IOError:
            self.logger.error("Could not open remote " "mapping configuration file")
            raise RemoteMappingLoadFailed

        if "playerMapping" not in remote_map:
            raise RemoteMappingLoadFailed("Invalid remote configuration!")

        # clear previous mapping
        self.player_mapping = {}
        self.master_mapping = {}

        # load player mapping
        for button, mapping in remote_map["playerMapping"].items():
            m = re.match(r"btn([0-9]+)", button)

            if m is not None:
                if int(m.group(1)) > 2:
                    # invalid button
                    raise RemoteMappingIllegalError(
                        "illegal" " button:" ' "{}"'.format(m.group(1))
                    )

                if mapping not in self.PLAYER_ACTIONS:
                    # invalid mapping
                    raise RemoteMappingIllegalError(
                        "illegal" " action:" ' "{}"'.format(mapping)
                    )

                # map button to action
                self.player_mapping[int(m.group(1))] = self.PLAYER_ACTIONS[mapping]

            else:
                # invalid entry
                raise RemoteMappingIllegalError("illegal button")

        # load master mapping
        for button, mapping in remote_map["masterMapping"].items():
            m = re.match(r"btn([0-9]+)", button)

            if m is not None:
                if int(m.group(1)) > 2:
                    # invalid button
                    raise RemoteMappingIllegalError(
                        "illegal" " button:" ' "{}"'.format(m.group(1))
                    )

                if mapping not in self.MASTER_ACTIONS:
                    # invalid mapping
                    raise RemoteMappingIllegalError(
                        "illegal" " action:" ' "{}"'.format(mapping)
                    )

                # map button to action
                self.master_mapping[int(m.group(1))] = self.MASTER_ACTIONS[mapping]

            else:
                # invalid entry
                raise RemoteMappingIllegalError("illegal button")

        # check that we have all necessary mappings
        if len(self.player_mapping) < 3:
            raise RemoteMappingLoadFailed("Player remote mapping is invalid!")
