"""Map SFX."""

import json


class SFXMappingLoadFailed(Exception):
    """Could not load mapping."""


class SFXUnknownEvent(Exception):
    """Unknown SFX."""


class SFXMappableEvents:
    """Game events which can be mapped."""

    GAME_END = 0
    COW_OUT = 1
    MUD_SKIPPER = 2


class SFXMapping:
    """Mapping logic."""

    MAPPABLE_EVENTS = {
        "gameEnd": SFXMappableEvents.GAME_END,
        "cowOut": SFXMappableEvents.COW_OUT,
        "mudSkipper": SFXMappableEvents.MUD_SKIPPER,
    }

    def __init__(self):
        """Initialize."""
        self.mapping = {}

    def load_config(self, filename):
        """Load configuration.

        Args
        ----
        filename: str
           Path to configuration file
        """
        try:
            sfx_map_file = open(filename)
            sfx_map = json.loads(sfx_map_file.read())
            sfx_map_file.close()
        except IOError:
            raise SFXMappingLoadFailed(
                "Could not open " "sfx mapping configuration file"
            )
        self.parse_config(sfx_map)

    def parse_config(self, configuration):
        """Parse configuration."""
        new_mapping = {}
        if "sfxmap" not in configuration:
            raise SFXMappingLoadFailed("Configuration is invalid")

        for key, value in configuration["sfxmap"].items():
            if key not in self.MAPPABLE_EVENTS:
                continue

            new_mapping[self.MAPPABLE_EVENTS[key]] = value

        # if successful
        self.mapping = new_mapping

    def get_sfx(self, sfx):
        """Get SFX by event.

        Args
        ----
        sfx: SFXMappableEvents
           Event
        """
        if sfx in self.mapping:
            return self.mapping[sfx]

        raise SFXUnknownEvent
