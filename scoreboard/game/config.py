"""Load configuration file."""

import json
import logging

# defaults
_SCORE_ANNOUNCE_INTVAL_DEFAULT = 5
_PAIR_TIMEOUT_DEFAULT = 30
_SERVE_TIMEOUT_DEFAULT = 3
_GAME_DURATION_DEFAULT = 20


class ChainballGameConfiguration:
    """Configuration loader class."""

    def __init__(self):
        """Initialize."""
        self.logger = logging.getLogger("sboard.config")

        self.score_announce_interval = _SCORE_ANNOUNCE_INTVAL_DEFAULT
        self.pair_timeout = _PAIR_TIMEOUT_DEFAULT
        self.serve_timeout = _SERVE_TIMEOUT_DEFAULT
        self.game_duration = _GAME_DURATION_DEFAULT

    def load_config(self, filename):
        """Load configuration file.

        Args
        ----
        filename: str
           Configuration file path
        """
        try:
            with open(filename, "r") as f:
                config_data = json.load(f)
        except:
            self.logger.warning(
                "Could not load configuration file," "using defaults"
            )
            config_data = {}

        # load stuff
        if "scoreAnnounceInterval" in config_data:
            self.score_announce_interval = int(
                config_data["scoreAnnounceInterval"]
            )

        if "pairTimeout" in config_data:
            self.pair_timeout = int(config_data["pairTimeout"])

        if "serveTimeout" in config_data:
            self.serve_timeout = int(config_data["serveTimeout"])

        if "gameDurationMinutes" in config_data:
            self.game_duration = int(config_data["gameDurationMinutes"])
