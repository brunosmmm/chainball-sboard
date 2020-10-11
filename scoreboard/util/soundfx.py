"""SFX library and audio device handler."""

import base64
import logging
import os
import threading
from collections import deque

import pkg_resources
from scoreboard.util.configfiles import (
    CHAINBALL_CONFIGURATION,
    ChainBallConfigurationError,
)
from scoreboard.util.mopidy import (
    MopidyError,
    mopidy_is_playing,
    mopidy_pause,
    mopidy_play,
)
from scoreboard.util.spotify import (
    SpotifyError,
    get_spotify_play_state,
)

# sound hack on rpi
if CHAINBALL_CONFIGURATION.scoreboard.use_omx:
    from subprocess import CalledProcessError, check_call
else:
    from playsound import playsound


SFX_LOGGER = logging.getLogger("sboard.sfx")


class SFXDataError(Exception):
    """SFX data error."""


class GameSoundEffect(threading.Thread):
    """Thread that plays a sound."""

    def __init__(self, fxobj, idx=1, control_spotify=True):
        """Initialize."""
        super().__init__()
        self.fx = fxobj
        self.finished = False
        self._idx = idx
        self._spotify = control_spotify

    @property
    def control_spotify(self):
        """Get whether playback should be controlled."""
        return self._spotify

    @property
    def idx(self):
        """Get index."""
        return self._idx

    def run(self):
        """Play SFX."""
        if self.fx is None:
            self.finished = True
            return

        if CHAINBALL_CONFIGURATION.scoreboard.use_omx:
            try:
                check_call(["omxplayer", "--no-keys", "-o", "local", self.fx])
            except CalledProcessError:
                SFX_LOGGER.error("could not play SFX: {}".format(self.fx))
        else:
            try:
                playsound(self.fx)
            except Exception as ex:
                SFX_LOGGER.error(
                    "could not play SFX: {}, got: {}".format(self.fx, ex)
                )

        self.finished = True
        # end


class GameSFXHandlerStates:
    """Handler states."""

    IDLE = 0
    PLAYING = 1


class GameSFXHandler:
    """SFX Handler."""

    def __init__(self):
        """Initialize."""

        self.state = GameSFXHandlerStates.IDLE
        self.current_fx = None
        self._paused_by_sboard = False

        self._fx_queue = deque()
        self._has_audio = True
        self._resume_spotify_playback = False

        # build library
        self.fx_dict = {}
        self.fx_desc = {}
        try:
            sfx_config = CHAINBALL_CONFIGURATION.retrieve_configuration("sfx")
        except ChainBallConfigurationError:
            SFX_LOGGER.error("Invalid SFX library configuration file")
            return

        # check path, create if doesnt exist
        if not os.path.isabs(sfx_config.sfxpath):
            sfx_path = os.path.join(".", sfx_config.sfxpath)
        else:
            sfx_path = sfx_config.sfxpath
        if not os.path.exists(sfx_path):
            SFX_LOGGER.warning("sfx database path does not exist")
            try:
                os.makedirs(sfx_path)
            except OSError:
                SFX_LOGGER.error("cannot create sfx database path")

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

        SFX_LOGGER.debug("loaded {} SFX files".format(len(self.fx_dict)))

    def play_fx(self, *fx_list):
        """Play SFX."""
        if self._has_audio is False:
            SFX_LOGGER.warning("no audio device, cannot play sfx")
            return
        # return
        try:
            spotify_playing = get_spotify_play_state()
        except SpotifyError:
            # ignore
            spotify_playing = False
        offset = 0
        for idx, fx in enumerate(fx_list):
            if fx in self.fx_dict:
                # play
                self._fx_queue.append(
                    (
                        GameSoundEffect(
                            self.fx_dict[fx],
                            len(fx_list) - idx + offset,
                            control_spotify=spotify_playing,
                        )
                    )
                )
                # self.state = GameSFXHandlerStates.PLAYING
            else:
                offset += 1
                continue

    def handle(self):
        """Handle play state machine."""
        if self.current_fx is not None and not self.current_fx.finished:
            return
        try:
            next_fx = self._fx_queue.popleft()
            self.current_fx = next_fx
            self.state = GameSFXHandlerStates.PLAYING

            # next_fx.start()
        except IndexError:
            # queue is empty
            self.state = GameSFXHandlerStates.IDLE
            if (
                CHAINBALL_CONFIGURATION.scoreboard.control_mopidy
                and self.current_fx is not None
                and self._paused_by_sboard
            ):
                try:
                    is_playing = mopidy_is_playing()
                    if is_playing is False:
                        mopidy_play()
                        self._paused_by_sboard = False
                except MopidyError:
                    pass
            return

        # first try to get spotify state
        if CHAINBALL_CONFIGURATION.scoreboard.control_mopidy:
            try:
                is_playing = mopidy_is_playing()
                if is_playing:
                    mopidy_pause()
                    self._paused_by_sboard = True
            except MopidyError:
                pass

        next_fx.start()

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
