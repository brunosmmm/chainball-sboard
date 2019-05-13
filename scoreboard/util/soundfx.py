"""SFX library and audio device handler."""

import threading
import logging
import os
import pkg_resources
from playsound import playsound
from scoreboard.util.configfiles import ChainBallConfigurationError


class GameSoundEffect(threading.Thread):
    """Thread that plays a sound."""

    def __init__(self, fxobj):
        """Initialize."""
        super(GameSoundEffect, self).__init__()
        self.fx = fxobj
        self.finished = False

    def run(self):
        """Play SFX."""
        playsound(self.fx)

        self.finished = True
        # end


class GameSFXHandlerStates(object):
    """Handler states."""

    IDLE = 0
    PLAYING = 1


class GameSFXHandler(object):
    """SFX Handler."""

    def __init__(self, configuration):
        """Initialize."""
        self.logger = logging.getLogger("sboard.sfx")

        self.state = GameSFXHandlerStates.IDLE
        self.current_fx = None

        self._has_audio = True

        # build library
        self.fx_dict = {}
        self.fx_desc = {}
        try:
            sfx_config = configuration.retrieve_configuration("sfx")
        except ChainBallConfigurationError:
            self.logger.error("Invalid SFX library configuration file")
            return

        self.fx_dict = {}
        for name, sfx in sfx_config["sfxlib"].items():
            builtin = sfx.get("builtin", False)
            if builtin:
                data_path = pkg_resources.resource_filename(
                    "scoreboard", "data"
                )
                path = os.path.join(data_path, "sfx", sfx["file"])
            else:
                path = os.path.join(
                    os.getcwd(), sfx_config["sfxpath"], sfx["file"]
                )
            if self._has_audio:
                self.fx_dict[name] = path

        self.fx_desc = {
            x: y["description"] for x, y in sfx_config["sfxlib"].items()
        }

        self.logger.debug("loaded {} SFX files".format(len(self.fx_dict)))

    def play_fx(self, fx):
        """Play SFX."""
        if self._has_audio is False:
            self.logger.warning("no audio device, cannot play sfx")
            return
        # return
        if fx in self.fx_dict:
            self.current_fx = GameSoundEffect(self.fx_dict[fx])

            # play
            self.logger.debug("Playing {}".format(fx))
            self.current_fx.start()
            self.state = GameSFXHandlerStates.PLAYING
        else:
            raise KeyError("no such sound effect: {}".format(fx))

    def handle(self):
        """Handle play state machine."""
        if self.current_fx is not None:
            if self.current_fx.finished:
                self.state = GameSFXHandlerStates.IDLE

    def get_available_sfx(self):
        """Get available SFXs."""
        return self.fx_desc

    def get_sfx_description(self, fx_name):
        """Get SFX description."""
        if fx_name in self.fx_desc:
            return self.fx_desc[fx_name]

        return None
