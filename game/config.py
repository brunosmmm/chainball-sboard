import json
import logging

# defaults
_SCORE_ANNOUNCE_INTVAL_DEFAULT = 5
_PAIR_TIMEOUT_DEFAULT = 30
_SERVE_TIMEOUT_DEFAULT = 3


class ChainballGameConfiguration(object):
    def __init__(self):

        self.logger = logging.getLogger('sboard.config')

        self.score_announce_interval = _SCORE_ANNOUNCE_INTVAL_DEFAULT
        self.pair_timeout = _PAIR_TIMEOUT_DEFAULT
        self.serve_timeout = _SERVE_TIMEOUT_DEFAULT

    def load_config(self, filename):

        try:
            with open(filename, 'r') as f:
                config_data = json.load(f)
        except:
            self.logger.warning('Could not load configuration file,'
                                'using defaults')

        # load stuff
        if 'scoreAnnounceInterval' in config_data:
            self.score_announce_interval = int(config_data['scoreAnnounceInterval'])

        if 'pairTimeout' in config_data:
            self.pair_timeout = int(config_data['pairTimeout'])

        if 'serveTimeout' in config_data:
            self.serve_timeout = int(config_data['serveTimeout'])
