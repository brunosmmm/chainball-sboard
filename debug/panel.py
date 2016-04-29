from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.uix.bubble import Bubble, BubbleButton
import requests
import logging
import json
import argparse
from miscui import ScoreSpinner, RootFinderMixin
import json

SCOREBOARD_LOCATION = 'http://localhost:8080'


class PlayerActions(Bubble, RootFinderMixin):

    def __init__(self, *args, **kwargs):
        super(PlayerActions, self).__init__(*args, **kwargs)

        self.player = kwargs['player']
        self.pos = kwargs['position']
        self.size = kwargs['size']
        self.size_hint = (None, None)

        self.add_btn = BubbleButton(on_press=self.add_player,
                                    text='Add player',
                                    disabled=kwargs['is_registered'])
        self.rm_btn = BubbleButton(on_press=self.remove_player,
                                   text='Remove player',
                                   disabled=not kwargs['is_registered'])
        self.pair_btn = BubbleButton(on_press=self.pair_remote,
                                     text='Pair remote',
                                     disabled=not kwargs['is_registered'])
        self.add_widget(self.add_btn)
        self.add_widget(self.rm_btn)
        self.add_widget(self.pair_btn)

    def add_player(self, *args):
        #r = requests.post(SCOREBOARD_LOCATION+'/control/pregister', json=)
        self.find_root().kill_pbubb()

    def remove_player(self, *args):
        r = requests.post(SCOREBOARD_LOCATION+'/control/punregister',
                          data=('playerNumber={}'.format(self.player)))

        self.find_root().kill_pbubb()

    def pair_remote(self, *args):
        self.find_root().kill_pbubb()


class RootWidget(FloatLayout):

    def __init__(self, *args, **kwargs):
        super(RootWidget, self).__init__(*args, **kwargs)

        # scoreboard data
        self.sfx_list = {}
        self.sfx_reverse_list = {}
        self.game_persist_list = []
        self.registered_player_list = []

        # flags
        self.stop_refreshing = False
        self.pbubb_open = False
        self.pbubb_player = None
        self.game_running = False

        Clock.schedule_interval(self.refresh_status, 1)

    def disable_app(self):
        self.disabled = True

    def enable_app(self):
        self.disabled = False

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

    def force_pairing(self):

        for p in range(0, self.player_num):
            #force pairing
            r = requests.get(SCOREBOARD_LOCATION+'/debug/fpair/{},{}'.format(p, p+1))

    def do_sfx_play(self, * args):

        if self.ids['sfxname'].text not in self.sfx_reverse_list:
            # try directly
            sfx_name = self.ids['sfxname'].text
        else:
            sfx_name = self.sfx_reverse_list[self.ids['sfxname'].text]

        r = requests.get(SCOREBOARD_LOCATION+'/debug/sfx/{}'.format(sfx_name))

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
            score = int(self.ids['pscore{}'.format(player)].text)
        except (TypeError, ValueError):
            print 'Invalid score input'
            return

        if score > 5 or score < -10:
            print 'Invalid score input'
            self.ids['setscore{}'.format(player)].text = ''
            return

        r = requests.get(SCOREBOARD_LOCATION+'/debug/setscore/{},{}'.format(player, score))

        try:
            response = r.json()
        except:
            return

        if response['status'] == 'error':
            print 'Could not set score, returned {}'.format(response['error'])

    def do_set_turn(self, player):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/setturn/{}'.format(player))

    def do_set_turn_1(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/setturn/0')

    def do_set_turn_2(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/setturn/1')

    def do_set_turn_3(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/setturn/2')

    def do_set_turn_4(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/setturn/3')

    def one_shot_refresh(self):
        try:
            r = requests.get(SCOREBOARD_LOCATION+'/status/sfxlist')
            status = r.json()
        except:
            print 'error getting SFX List'
            return

        if status['status'] != 'ok':
            print 'error getting SFX List'
            return

        self.sfx_list = status['sfx_list']

        # update spinner
        self.ids['sfxname'].values = [v if v is not None else k for k, v in self.sfx_list.iteritems()]
        self.ids['sfxname'].text = self.ids['sfxname'].values[0]

        # create SFX reverse lookup dictionary
        self.sfx_reverse_list = {}
        for k, v in self.sfx_list.iteritems():
            if v is not None:
                self.sfx_reverse_list[v] = k

        # get game persistance data
        try:
            r = requests.get(SCOREBOARD_LOCATION+'/persist/game_list')
            status = r.json()
        except:
            print 'error getting game persistance'
            return

        self.game_persist_list = status['game_list']
        # update spinner
        self.ids['gpersist'].values = sorted(self.game_persist_list)
        self.ids['gpersist'].disabled = False

    def refresh_status(self, *args):

        if self.stop_refreshing is True:
            return

        # try to contact scoreboard
        try:
            r = requests.get(SCOREBOARD_LOCATION+'/status/all', timeout=1)
            status = r.json()
            if self.disabled:
                self.enable_app()
                self.one_shot_refresh()
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout):
            # disable
            self.disable_app()
            return

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
            self.game_running = True
            self.ids['statuslabel'].text = 'Running'
            server = int(json_data['serving'])
            for i in range(0, 4):
                self.ids['psettings{}'.format(i)].disabled = False
                self.ids['pscore{}'.format(i)].disabled = False
                self.ids['pindirect{}'.format(i)].disabled = False
                self.ids['preferee{}'.format(i)].disabled = False
        elif json_data['game'] == 'stopped':
            self.game_running = False
            self.ids['statuslabel'].text = 'Stopped'
            for i in range(0, 4):
                self.ids['psettings{}'.format(i)].disabled = False
                self.ids['pname{}'.format(i)].disabled = False
                self.ids['pscore{}'.format(i)].disabled = True
                self.ids['pindirect{}'.format(i)].disabled = True
                self.ids['preferee{}'.format(i)].disabled = True

        json_data = status['players']
        self.player_num = len(json_data)
        self.registered_player_list = json_data.keys()
        for i in range(0,4):
            if str(i) in json_data:
                self.ids['pname{}'.format(i)].text = json_data[str(i)]
            else:
                self.ids['pname{}'.format(i)].text = ''

        json_data = status['scores']
        if json_data['status'] == 'error':
            for i in range(0,4):
                self.ids['pscore{}'.format(i)].update_score('-')

        for i in range(0,4):
            if str(i) in json_data and i < self.player_num:
                self.ids['pscore{}'.format(i)].update_score(str(json_data[str(i)]))
                if int(json_data[str(i)]) == -10:
                    self.ids['psettings{}'.format(i)].disabled = True
            elif self.game_running is True:
                self.ids['pscore{}'.format(i)].update_score('-')
                self.ids['pname{}'.format(i)].disabled = True
                self.ids['pindirect{}'.format(i)].disabled = True
                self.ids['preferee{}'.format(i)].disabled = True

        if server > -1:
            player_name = self.ids['pname{}'.format(server)].text
            self.ids['pname{}'.format(server)].text = '[color=ff0000]{}[/color]'.format(player_name)

        json_data = status['timer']
        if 'status' in json_data:
            if json_data['status'] == 'error':
                return

        self.ids['timerlabel'].text ='{:0>2d}'.format(json_data['minutes']) + ':' + '{:0>2d}'.format(json_data['seconds'])


    def register_scoring_event(self, evt_type, player):
        r = requests.get(SCOREBOARD_LOCATION+'/control/scoreevt/{},{}'.format(player, evt_type))

    # beware of very convoluted logic below
    def handle_player_button(self, player):

        if self.game_running:
            self.do_set_turn(player)
            return

        if not hasattr(self, 'pbubb'):
            butpos = self.ids['pname{}'.format(player)].pos
            butsize = self.ids['pname{}'.format(player)].size
            bubsize = [320, 100]
            bubpos = []
            bubpos.append(butpos[0] + butsize[0]/2 - bubsize[0]/2)
            bubpos.append(butpos[1] - butsize[1]/2 + bubsize[1])

            is_registered = str(player) in self.registered_player_list
            self.pbubb = PlayerActions(player=player,
                                       position=bubpos,
                                       size=bubsize,
                                       is_registered=is_registered)
            self.pbubb_open = False
            self.pbubb_player = player
        else:
            self.pbubb_player = player

    def kill_pbubb(self):
        self.pbubb_open = False
        self.remove_widget(self.pbubb)
        pbubb_cur_player = self.pbubb.player
        del self.pbubb

        return pbubb_cur_player

    def on_touch_down(self, touch):
        super(RootWidget, self).on_touch_down(touch)

        if hasattr(self, 'pbubb'):
            pbubb_cur_player = None
            if self.pbubb_open:
                if self.pbubb.collide_point(*touch.pos) is False:
                    # clicked outside of bubble
                    pbubb_cur_player = self.kill_pbubb()
                    if self.pbubb_player != pbubb_cur_player:
                        # create new bubble now (clicked onther player button)
                        self.handle_player_button(self.pbubb_player)
                        self.pbubb_open = True
                        self.add_widget(self.pbubb)
            else:
                self.pbubb_open = True
                self.add_widget(self.pbubb)


class SimpleboardDebugPanel(App):

    def __init__(self, *args, **kwargs):
        super(SimpleboardDebugPanel, self).__init__(*args, **kwargs)

        self.root = RootWidget()

    def build(self):
        return self.root


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('address', nargs='?')
    parser.add_argument('port', nargs='?')
    parser.set_defaults(address='1.1.1.1', port=80)

    args = parser.parse_args()

    SCOREBOARD_LOCATION = 'http://{}:{}'.format(args.address, args.port)

    Builder.load_file('panel.kv')
    panel = SimpleboardDebugPanel()

    panel.run()
