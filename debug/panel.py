from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.clock import Clock
import requests
import logging
import json
import argparse

SCOREBOARD_LOCATION = 'http://localhost:8080'


class RootWidget(FloatLayout):

    def __init__(self, *args, **kwargs):
        super(RootWidget, self).__init__(*args, **kwargs)

        Clock.schedule_interval(self.refresh_status, 1)

    def do_pause_unpause(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/control/pauseunpause')

        try:
            status = r.json()
        except:
            print 'could not parse response'
            return

        if status['status'] == 'error':
            print 'could not pause/unpause timer, got: {}'.format(status['error'])

    def do_start_game(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/control/gbegin')

        try:
            status = r.json()
        except:
            print 'could not parse response'
            return

        if status['status'] == 'error':
            print 'could not start game, got: {}'.format(status['error'])

    def do_end_game(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/control/gend')

        try:
            status = r.json()
        except:
            print 'could not parse response'
            return

        if status['status'] == 'error':
            print 'could not stop game, got: {}'.format(status['error'])

    def do_debug_setup2(self, *args):
        self._do_debug_setup(2)

    def do_debug_setup4(self, *args):
        self._do_debug_setup(4)

    def do_remove_all(self, *args):

        r = requests.get(SCOREBOARD_LOCATION+'/status/players')

        try:
            players = r.json()
        except Exception:
            print 'could not remove players'
            return

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        for player in players:
            player_data = {'playerNumber' : player}
            r = requests.post(SCOREBOARD_LOCATION+'/control/punregister', data=player_data, headers=headers)

            try:
                status = r.json()
            except Exception:
                print 'Could not unregister player {}'.format(player)
                continue

            if status['status'] == 'error':
                print 'Could not unregister player {}, got: {}'.format(player, status['error'])
                continue

    def _do_debug_setup(self, player_num):

        player_names = ["A", "B", "C", "D"]

        #register some players

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        for p in range(0, player_num):

            player_data = {'panelTxt' : player_names[p], 'webTxt' : player_names[p]}
            r = requests.post(SCOREBOARD_LOCATION+'/control/pregister', data=player_data, headers=headers)

            try:
                response = r.json()
                if response['status'] == 'error':
                    raise Exception
            except Exception:
                print 'Could not setup successfully, returned: {}'.format(response['error'])
                continue

            player_num = int(response['playerNum'])

            #force pairing
            r = requests.get(SCOREBOARD_LOCATION+'/debug/fpair/{},{}'.format(player_num, player_num+1))

    def do_sfx_play(self, * args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/sfx/{}'.format(self.ids['sfxname'].text))

        try:
            status = r.json()
        except:
            print 'could not parse response'
            return

        if status['status'] == 'error':
            print 'Could not play SFX, got: {}'.format(status['error'])

    def do_test_score_1(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/scoretest/0')

    def do_test_score_2(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/scoretest/1')

    def do_test_score_3(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/scoretest/2')

    def do_test_score_4(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/scoretest/3')

    def do_announce(self, *args):
        heading = self.ids['ann_header'].text[:6]
        text = self.ids['ann_text'].text[:6]

        r = requests.get(SCOREBOARD_LOCATION+'/debug/announce/{},{},{}'.format(heading, text, 2))

    def do_incr_score(self, pnum):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/sincr/{}'.format(pnum))

    def do_decr_score(self, pnum):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/sdecr/{}'.format(pnum))

    def do_force_serve(self, pnum):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/pass')

    def do_set_score(self, player):

        try:
            score = int(self.ids['setscore{}'.format(player)].text)
        except (TypeError, ValueError):
            print 'Invalid score input'
            return

        if score > 5 or score < -10:
            print 'Invalid score input'
            self.score_input.text = ''
            return

        r = requests.get(SCOREBOARD_LOCATION+'/debug/setscore/{},{}'.format(player, score))

        try:
            response = r.json()
        except:
            return

        if response['status'] == 'error':
            print 'Could not set score, returned {}'.format(response['error'])

    def do_set_turn_1(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/setturn/0')

    def do_set_turn_2(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/setturn/1')

    def do_set_turn_3(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/setturn/2')

    def do_set_turn_4(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/setturn/3')

    def refresh_status(self, *args):

        r = requests.get(SCOREBOARD_LOCATION+'/status/all')
        status = r.json()

        #first look at board status
        json_data = status['board']
        if json_data['status'] == 'error':
            self.ids['statuslabel'].text = 'Scoreboard ERROR'
            return

        #get game status
        json_data = status['game']
        if json_data['status'] == 'error':
            self.ids['statuslabel'].text = 'Game ERROR'
            return

        server = -1
        if json_data['game'] == 'started':
            self.ids['statuslabel'].text = 'Game running'
            server = int(json_data['serving'])
        elif json_data['game'] == 'stopped':
            self.ids['statuslabel'].text = 'Game stopped'

        json_data = status['players']
        player_num = len(json_data)
        for i in range(0,4):
            if str(i) in json_data:
                self.ids['pname{}'.format(i)].text = json_data[str(i)]
            else:
                self.ids['pname{}'.format(i)].text = ''

        json_data = status['scores']
        if json_data['status'] == 'error':
            for i in range(0,4):
                self.ids['pscore{}'.format(i)].text = ''

        for i in range(0,4):
            if str(i) in json_data and i < player_num:
                self.ids['pscore{}'.format(i)].text = str(json_data[str(i)])
            else:
                self.ids['pscore{}'.format(i)].text = ''

        if server > -1:
            player_name = self.ids['pname{}'.format(server)].text
            self.ids['pname{}'.format(server)].text = '[color=ff0000]{}[/color]'.format(player_name)

        json_data = status['timer']
        if 'status' in json_data:
            if json_data['status'] == 'error':
                return

        self.ids['timerlabel'].text ='{:0>2d}'.format(json_data['minutes']) + ':' + '{:0>2d}'.format(json_data['seconds'])

class SimpleboardDebugPanel(App):

    def build(self):
        return RootWidget()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('address')
    parser.add_argument('port')

    args = parser.parse_args()

    SCOREBOARD_LOCATION = 'http://{}:{}'.format(args.address, args.port)

    #try to see if the the scoreboard is running
    try:
        r = requests.get(SCOREBOARD_LOCATION+'/status/board')
    except requests.exceptions.ConnectionError:
        print 'ERROR: Could not connect to the scoreboard'
        exit(0)

    Builder.load_file('panel.kv')
    SimpleboardDebugPanel().run()
