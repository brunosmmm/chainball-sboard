import threading
import pygame
import logging
import time

SOUND_FX_LIB = {'buzzer' : 'sfx/buzzer.wav',
                'out' : 'sfx/out.wav'}

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

        pygame.mixer.init(frequency=44100)

        self.fx_dict = dict([(x, pygame.mixer.Sound(y)) for x, y in SOUND_FX_LIB.iteritems()])

    def play_fx(self, fx):

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
