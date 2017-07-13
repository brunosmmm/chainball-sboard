import threading
import pygame
import logging
import time
import json

class GameSoundEffect(threading.Thread):

    def __init__(self, fxobj):
        super(GameSoundEffect, self).__init__()
        self.fx = fxobj
        self.finished = False

    def run(self):
        #play effect
        channel = self.fx.play()
        while channel.get_busy():
            time.sleep(0.01)

        self.finished = True
        #end

class GameSFXHandlerStates(object):
    IDLE = 0
    PLAYING = 1

class GameSFXHandler(object):

    def __init__(self):

        self.logger = logging.getLogger('sboard.sfx')

        self.state = GameSFXHandlerStates.IDLE
        self.current_fx = None

        try:
            pygame.mixer.init(frequency=44100)
            self._has_audio = True
        except pygame.error:
            self.logger.error('Failed to acquire audio device.')
            self._has_audio = False

        #build library
        self.fx_dict = {}
        self.fx_desc = {}
        try:
            sfx_config_contents = open('conf/sfx.json')
            sfx_config = json.loads(sfx_config_contents.read())
            sfx_config_contents.close()
        except IOError:
            #no library, nothing to do
            self.logger.error('Could not open SFX library configuration file')
            return
        except KeyError:
            self.logger.error('Invalid SFX library configuration file')
            return

        self.fx_dict = dict([(x, pygame.mixer.Sound(sfx_config['sfxpath']+'/'+y['file'])) for x, y in sfx_config['sfxlib'].items()])

        self.fx_desc = dict([(x, y['description']) for x, y in sfx_config['sfxlib'].items()])

        self.logger.debug('loaded {} SFX files'.format(len(self.fx_dict)))

    def play_fx(self, fx):
        if self._has_audio is False:
            self.logger.warning('no audio device, cannot play sfx')
            return
        #return
        if fx in self.fx_dict:
            self.current_fx = GameSoundEffect(self.fx_dict[fx])

            #play
            self.logger.debug('Playing {}'.format(fx))
            self.current_fx.start()
            self.state = GameSFXHandlerStates.PLAYING
        else:
            raise KeyError('no such sound effect: {}'.format(fx))


    def handle(self):

        if self.current_fx != None:
            if self.current_fx.finished:
                self.state = GameSFXHandlerStates.IDLE

    def get_available_sfx(self):
        return self.fx_desc

    def get_sfx_description(self, fx_name):
        if fx_name in self.fx_desc:
            return self.fx_desc[fx_name]

        return None
