import re
import json

class SFXMappingLoadFailed(Exception):
    pass

class SFXUnknownEvent(Exception):
    pass

class SFXMappableEvents(object):
    GAME_END = 0
    COW_OUT = 1

class SFXMapping(object):
    MAPPABLE_EVENTS = {"gameEnd" : SFXMappableEvents.GAME_END,
                       "cowOut" : SFXMappableEvents.COW_OUT}
    def __init__(self):

        self.mapping = {}

    def load_config(self, filename):
        try:
            sfx_map_file = open(filename)
            sfx_map = json.loads(sfx_map_file.read())
            sfx_map_file.close()
        except IOError:
            raise SFXMappingLoadFailed('Could not open sfx mapping configuration file')

        if "sfxmap" not in sfx_map:
            raise SFXMappingLoadFailed('Configuration is invalid')

        for key, value in sfx_map['sfxmap'].iteritems():
            if key not in self.MAPPABLE_EVENTS:
                continue

            self.mapping[self.MAPPABLE_EVENTS[key]] = value

    def get_sfx(self, sfx):
        if sfx in self.mapping:
            return self.mapping[sfx]

        raise SFXUnknownEvent
