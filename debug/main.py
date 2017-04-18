from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.uix.bubble import Bubble, BubbleButton
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
import requests
import argparse
from threading import Thread
from miscui import ScoreSpinner, RootFinderMixin

class PanelUpdater(Thread):

    def __init__(self, *args, **kwargs):
        super(PanelUpdater, self).__init__(*args)

        self.scoreboard_address = kwargs['address']
        self.root = kwargs['root']

    def run(self):

        if self.root.stop_refreshing is True:
            return

        # try to contact scoreboard
        try:
            r = requests.get(self.root.scoreboard_address+'/status/all', timeout=1)
            status = r.json()
            if self.root.disconnected:
                self.root.enable_app()
                self.root.one_shot_refresh()
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout):
            # disable
            self.root.disable_app()
            return

        #first look at board status
        json_data = status['board']
        if json_data['status'] == 'error':
            self.root.ids['statuslabel'].text = 'Scoreboard ERROR'
            return

        #get game status
        json_data = status['game']
        if json_data['status'] == 'error':
            self.root.ids['statuslabel'].text = 'Game ERROR'
            return

        server = -1
        if json_data['game'] == 'started':
            self.root.game_running = True
            self.root.game_paused = False
            self.root.ids['statuslabel'].text = 'Running'
            server = int(json_data['serving'])
            for i in range(0, 4):
                self.root.ids['psettings{}'.format(i)].disabled = False
                self.root.ids['pscore{}'.format(i)].disabled = False
                self.root.ids['pindirect{}'.format(i)].disabled = False
                self.root.ids['preferee{}'.format(i)].disabled = False
        elif json_data['game'] == 'stopped' or json_data['game'] == 'paused':
            self.root.game_running = False
            if json_data['game'] == 'stopped':
                self.root.ids['statuslabel'].text = 'Stopped'
                self.root.game_paused = False
            else:
                self.root.ids['statuslabel'].text = 'Paused'
                self.root.game_paused = True
            for i in range(0, 4):
                self.root.ids['psettings{}'.format(i)].disabled = False
                self.root.ids['pname{}'.format(i)].disabled = False
                self.root.ids['pscore{}'.format(i)].disabled = True
                self.root.ids['pindirect{}'.format(i)].disabled = True
                self.root.ids['preferee{}'.format(i)].disabled = True

        json_data = status['players']
        self.root.player_num = len(json_data)
        self.root.registered_player_list = json_data
        for i in range(0,4):
            if str(i) in json_data:
                self.root.ids['pname{}'.format(i)].text = json_data[str(i)]['web_txt']
            else:
                self.root.ids['pname{}'.format(i)].text = ''

        json_data = status['scores']
        if json_data['status'] == 'error':
            for i in range(0,4):
                self.root.ids['pscore{}'.format(i)].update_score('-')

        for i in range(0,4):
            if str(i) in json_data and i < self.root.player_num:
                self.root.ids['pscore{}'.format(i)].update_score(str(json_data[str(i)]))
                if int(json_data[str(i)]) == -10:
                    self.root.ids['psettings{}'.format(i)].disabled = True
            elif self.root.game_running is True:
                self.root.ids['pscore{}'.format(i)].update_score('-')
                self.root.ids['pname{}'.format(i)].disabled = True
                self.root.ids['pindirect{}'.format(i)].disabled = True
                self.root.ids['preferee{}'.format(i)].disabled = True

        if server > -1:
            player_name = self.root.ids['pname{}'.format(server)].text
            self.root.ids['pname{}'.format(server)].text = '[color=ff0000]{}[/color]'.format(player_name)

        json_data = status['timer']
        if 'status' in json_data:
            if json_data['status'] == 'error':
                return

        self.root.ids['timerlabel'].text ='{:0>2d}'.format(json_data['minutes']) + ':' + '{:0>2d}'.format(json_data['seconds'])


class PlayerActions(Bubble, RootFinderMixin):

    def __init__(self, *args, **kwargs):
        super(PlayerActions, self).__init__(*args, **kwargs)

        self.player = kwargs['player']
        self.pos = kwargs['position']
        self.size = kwargs['size']
        self.is_paired = kwargs['is_paired']
        self.game_paused = kwargs['is_paused']
        self.scoreboard_address = kwargs['address']
        self.size_hint = (None, None)

        self.add_btn = BubbleButton(on_press=self.add_player,
                                    text='Add player',
                                    disabled=kwargs['is_registered'] or kwargs['is_paused'])
        self.rm_btn = BubbleButton(on_press=self.remove_player,
                                   text='Remove player',
                                   disabled=not kwargs['is_registered'] or kwargs['is_paused'])
        pair_txt = 'Unpair remote' if self.is_paired else 'Pair remote'
        self.pair_btn = BubbleButton(on_press=self.pair_remote,
                                     text=pair_txt,
                                     disabled=not kwargs['is_registered'])
        self.add_widget(self.add_btn)
        self.add_widget(self.rm_btn)
        self.add_widget(self.pair_btn)

    def _register_player(self, *args):

        panel_txt = self.ptxt.text
        web_txt = self.wtxt.text
        r = requests.post(self.scoreboard_address+'/control/pregister',
                          data={#'playerNum': self.player,
                                'panelTxt': panel_txt,
                                'webTxt': web_txt})
        # get status

        # kill popup
        self.popup.dismiss()

    def _add_dismiss(self, *args):
        del self.popup
        del self.ptxt
        del self.wtxt

    def add_player(self, *args):
        #r = requests.post(self.scoreboard_address+'/control/pregister', json=)

        # build popup contents
        box = BoxLayout(orientation='vertical', spacing=2)
        box.add_widget(Label(text='Full player name:'))
        self.wtxt = TextInput()
        box.add_widget(self.wtxt)
        box.add_widget(Label(text='Panel display name:'))
        self.ptxt = TextInput()
        box.add_widget(self.ptxt)

        addbut = Button(text='Add',
                        on_press=self._register_player)
        box.add_widget(addbut)

        # build popup and show
        self.popup = Popup(title='Add player',
                           content=box,
                           size_hint=(0.4, 0.4),
                           on_dismiss=self._add_dismiss)
        self.find_root().kill_pbubb()
        self.popup.open()

    def remove_player(self, *args):
        r = requests.post(self.scoreboard_address+'/control/punregister',
                          data=('playerNumber={}'.format(self.player)))

        self.find_root().kill_pbubb()

    def pair_remote(self, *args):

        if self.is_paired:
            # unpair, easy
            r = requests.post(self.scoreboard_address+'/control/runpair',
                              data=('playerNumber={}'.format(self.player)))
        else:
            pass

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
        self.game_paused = False
        self.disconnected = True

        self.scoreboard_address = kwargs['address']
        Clock.schedule_interval(self.refresh_status, 1)

    def disable_app(self):
        #self.disabled = True
        self.ids['gamectrltab'].disabled = True
        self.ids['debugtab'].disabled = True
        self.ids['saveddatatab'].disabled = True
        self.ids['gamesetuptab'].disabled = True
        self.disconnected = True

    def enable_app(self):
        self.ids['gamectrltab'].disabled = False
        self.ids['debugtab'].disabled = False
        self.ids['saveddatatab'].disabled = False
        self.ids['gamesetuptab'].disabled = False
        self.disconnected = False

    def do_pause_unpause(self, *args):
        r = requests.get(self.scoreboard_address+'/control/pauseunpause')

        try:
            status = r.json()
        except:
            print('could not parse response')
            return

        if status['status'] == 'error':
            print('could not pause/unpause timer, got: {}'.format(status['error']))
            popup = Popup(title='Error!',
                          content=Label(text=status['error']),
                          size_hint=(0.25,0.25))
            popup.open()

    def do_start_game(self, *args):
        r = requests.get(self.scoreboard_address+'/control/gbegin')

        try:
            status = r.json()
        except:
            print('could not parse response')
            return

        if status['status'] == 'error':
            print('could not start game, got: {}'.format(status['error']))
            popup = Popup(title='Error!',
                          content=Label(text=status['error']),
                          size_hint=(0.25,0.25))
            popup.open()

    def do_end_game(self, *args):
        r = requests.get(self.scoreboard_address+'/control/gend')

        try:
            status = r.json()
        except:
            print ('could not parse response')
            return

        if status['status'] == 'error':
            print ('could not stop game, got: {}'.format(status['error']))
            popup = Popup(title='Error!',
                          content=Label(text=status['error']),
                          size_hint=(0.25,0.25))
            popup.open()

    def do_debug_setup2(self, *args):
        self._do_debug_setup(2)

    def do_debug_setup4(self, *args):
        self._do_debug_setup(4)

    def do_remove_all(self, *args):

        r = requests.get(self.scoreboard_address+'/status/players')

        try:
            players = r.json()
        except Exception:
            print ('could not remove players')
            return

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        for player in sorted(players)[::-1]:
            player_data = {'playerNumber' : player}
            r = requests.post(self.scoreboard_address+'/control/punregister', data=player_data, headers=headers)

            try:
                status = r.json()
            except Exception:
                print ('Could not unregister player {}'.format(player))
                continue

            if status['status'] == 'error':
                print ('Could not unregister player {}, got: {}'.format(player, status['error']))
                continue

    def _do_debug_setup(self, player_num):

        player_names = ["A", "B", "C", "D"]

        #register some players

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        for p in range(0, player_num):

            player_data = {'panelTxt' : player_names[p], 'webTxt' : player_names[p]}
            r = requests.post(self.scoreboard_address+'/control/pregister', data=player_data, headers=headers)

            try:
                response = r.json()
                if response['status'] == 'error':
                    raise Exception
            except Exception:
                print ('Could not setup successfully, returned: {}'.format(response['error']))
                continue

            player_num = int(response['playerNum'])

            #force pairing
            r = requests.get(self.scoreboard_address+'/debug/fpair/{},{}'.format(player_num, player_num+1))

    def force_pairing(self):

        for p in range(0, self.player_num):
            #force pairing
            r = requests.get(self.scoreboard_address+'/debug/fpair/{},{}'.format(p, p+1))

    def do_sfx_play(self, * args):

        if self.ids['sfxname'].text not in self.sfx_reverse_list:
            # try directly
            sfx_name = self.ids['sfxname'].text
        else:
            sfx_name = self.sfx_reverse_list[self.ids['sfxname'].text]

        r = requests.get(self.scoreboard_address+'/debug/sfx/{}'.format(sfx_name))

        try:
            status = r.json()
        except:
            print ('could not parse response')
            return

        if status['status'] == 'error':
            print ('Could not play SFX, got: {}'.format(status['error']))

    def do_test_score_1(self, *args):
        r = requests.get(self.scoreboard_address+'/debug/scoretest/0')

    def do_test_score_2(self, *args):
        r = requests.get(self.scoreboard_address+'/debug/scoretest/1')

    def do_test_score_3(self, *args):
        r = requests.get(self.scoreboard_address+'/debug/scoretest/2')

    def do_test_score_4(self, *args):
        r = requests.get(self.scoreboard_address+'/debug/scoretest/3')

    def do_announce(self, *args):
        heading = self.ids['ann_header'].text[:6]
        text = self.ids['ann_text'].text[:6]

        r = requests.get(self.scoreboard_address+'/debug/announce/{},{},{}'.format(heading, text, 2))

    def do_incr_score(self, pnum):
        r = requests.get(self.scoreboard_address+'/debug/sincr/{}'.format(pnum))

    def do_decr_score(self, pnum):
        r = requests.get(self.scoreboard_address+'/debug/sdecr/{}'.format(pnum))

    def do_force_serve(self, pnum):
        r = requests.get(self.scoreboard_address+'/debug/pass')

    def do_set_score(self, player):

        try:
            score = int(self.ids['pscore{}'.format(player)].text)
        except (TypeError, ValueError):
            print ('Invalid score input')
            return

        if score > 5 or score < -10:
            print ('Invalid score input')
            self.ids['setscore{}'.format(player)].text = ''
            return

        r = requests.get(self.scoreboard_address+'/debug/setscore/{},{}'.format(player, score))

        try:
            response = r.json()
        except:
            return

        if response['status'] == 'error':
            print ('Could not set score, returned {}'.format(response['error']))

    def do_set_turn(self, player):
        r = requests.get(self.scoreboard_address+'/debug/setturn/{}'.format(player))

    def do_set_turn_1(self, *args):
        r = requests.get(self.scoreboard_address+'/debug/setturn/0')

    def do_set_turn_2(self, *args):
        r = requests.get(self.scoreboard_address+'/debug/setturn/1')

    def do_set_turn_3(self, *args):
        r = requests.get(self.scoreboard_address+'/debug/setturn/2')

    def do_set_turn_4(self, *args):
        r = requests.get(self.scoreboard_address+'/debug/setturn/3')

    def one_shot_refresh(self):
        try:
            r = requests.get(self.scoreboard_address+'/status/sfxlist')
            status = r.json()
        except:
            print ('error getting SFX List')
            return

        if status['status'] != 'ok':
            print ('error getting SFX List')
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
            r = requests.get(self.scoreboard_address+'/persist/game_list')
            status = r.json()
        except:
            print ('error getting game persistance')
            return

        self.game_persist_list = status['game_list']
        # update spinner
        self.ids['gpersist'].values = sorted(self.game_persist_list)
        self.ids['gpersist'].disabled = False

    def refresh_status(self, *args):
        #hacky hack
        updater = PanelUpdater(address=self.scoreboard_address, root=self)

        updater.start()
        #updater.join()

    def register_scoring_event(self, evt_type, player):
        r = requests.get(self.scoreboard_address+'/control/scoreevt/{},{}'.format(player, evt_type))

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

            is_registered = str(player) in self.registered_player_list.keys()
            is_paired = False
            if is_registered:
                is_paired = self.registered_player_list[str(player)]['remote_id'] != None
            self.pbubb = PlayerActions(player=player,
                                       position=bubpos,
                                       size=bubsize,
                                       is_registered=is_registered,
                                       is_paired=is_paired,
                                       is_paused=self.game_paused,
                                       address=self.scoreboard_address)
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

    def set_scoreboard_address(self):
        # do error checking?
        self.scoreboard_address = 'http://{}:{}'.format(self.ids['scorebrdip'].text,
                                                        self.ids['scorebrdport'].text)


class SimpleboardDebugPanel(App):

    def __init__(self, *args, **kwargs):
        super(SimpleboardDebugPanel, self).__init__(*args, **kwargs)

        self.root = RootWidget(address=kwargs['address'])

    def build(self):
        return self.root


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('address', nargs='?')
    parser.add_argument('port', nargs='?')
    parser.set_defaults(address='1.1.1.1', port=80)

    args = parser.parse_args()

    Builder.load_file('panel.kv')
    panel = SimpleboardDebugPanel(address='http://{}:{}'.format(args.address, args.port))

    panel.run()
