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

        self.parse_config(config_data)

    def parse_config(self, configuration):
        """Parse configuration."""
        if "scoreAnnounceInterval" in configuration:
            self.score_announce_interval = int(
                configuration["scoreAnnounceInterval"]
            )

        if "pairTimeout" in configuration:
            self.pair_timeout = int(configuration["pairTimeout"])

        if "serveTimeout" in configuration:
            self.serve_timeout = int(configuration["serveTimeout"])

        if "gameDurationMinutes" in configuration:
            self.game_duration = int(configuration["gameDurationMinutes"])
