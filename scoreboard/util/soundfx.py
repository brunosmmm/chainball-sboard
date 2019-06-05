"""SFX library and audio device handler."""

import threading
import logging
import os
import base64
import pkg_resources
from playsound import playsound
from scoreboard.util.configfiles import (
    CHAINBALL_CONFIGURATION,
    ChainBallConfigurationError,
)
from collections import deque


class SFXDataError(Exception):
    """SFX data error."""


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

    def __init__(self):
        """Initialize."""
        self.logger = logging.getLogger("sboard.sfx")

        self.state = GameSFXHandlerStates.IDLE
        self.current_fx = None

        self._fx_queue = deque()
        self._has_audio = True

        # build library
        self.fx_dict = {}
        self.fx_desc = {}
        try:
            sfx_config = CHAINBALL_CONFIGURATION.retrieve_configuration("sfx")
        except ChainBallConfigurationError:
            self.logger.error("Invalid SFX library configuration file")
            return

        # check path, create if doesnt exist
        if not os.path.isabs(sfx_config.sfxpath):
            sfx_path = os.path.join(".", sfx_config.sfxpath)
        if not os.path.exists(sfx_path):
            self.logger.warning("sfx database path does not exist")
            try:
                os.makedirs(sfx_path)
            except OSError:
                self.logger.error("cannot create sfx database path")

        self.fx_dict = {}
        for name, sfx in sfx_config["sfxlib"].items():
            builtin = sfx.get("builtin", False)
            if builtin:
                data_path = pkg_resources.resource_filename(
                    "scoreboard", "data"
                )
                path = os.path.join(data_path, "sfx", sfx["file"])
            else:
                path = os.path.join(sfx_path, sfx["file"])
            if self._has_audio:
                self.fx_dict[name] = path

        self.fx_desc = {
            x: y["description"] for x, y in sfx_config["sfxlib"].items()
        }

        self.fx_data_path = sfx_path

        self.logger.debug("loaded {} SFX files".format(len(self.fx_dict)))

    def play_fx(self, fx):
        """Play SFX."""
        if self._has_audio is False:
            self.logger.warning("no audio device, cannot play sfx")
            return
        # return
        if fx in self.fx_dict:

            # play
            self.logger.debug("Queuing {}".format(fx))
            self._fx_queue.append(GameSoundEffect(self.fx_dict[fx]))
            self.state = GameSFXHandlerStates.PLAYING
        else:
            raise KeyError("no such sound effect: {}".format(fx))

    def handle(self):
        """Handle play state machine."""
        if self.current_fx is not None and not self.current_fx.finished:
            return
        else:
            try:
                next_fx = self._fx_queue.popleft()
                self.current_fx = next_fx
                self.state = GameSFXHandlerStates.PLAYING
                next_fx.start()
            except IndexError:
                # queue is empty
                self.state = GameSFXHandlerStates.IDLE

    def get_available_sfx(self):
        """Get available SFXs."""
        return self.fx_desc

    def get_sfx_description(self, fx_name):
        """Get SFX description."""
        if fx_name in self.fx_desc:
            return self.fx_desc[fx_name]

        return None

    def insert_sfx_data(self, fx_name, fx_data):
        """Insert data."""
        # add to configuration
        sfx_data_bytes = base64.b64decode(fx_data)
        sfx_dest_path = os.path.join(self.fx_data_path, fx_name)
        try:
            with open(sfx_dest_path, "wb") as sfx_data_file:
                sfx_data_file.write(sfx_data_bytes)
        except OSError:
            raise SFXDataError("cannot save SFX data")

        self.fx_desc[fx_name] = "SFX_{}".format(fx_name)
        CHAINBALL_CONFIGURATION.sfx.sfxlib[fx_name] = {
            "file": fx_name,
            "description": "SFX_{}".format(fx_name),
            "builtin": False,
        }

    def commit_sfx_data(self):
        """Save to disk."""
        CHAINBALL_CONFIGURATION.sfx.save()


SFX_HANDLER = GameSFXHandler()
