from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import requests
import logging
import json
import argparse

SCOREBOARD_LOCATION = 'http://localhost:8080'

class FlowControl(BoxLayout):

    def __init__(self, **kwargs):
        super(FlowControl, self).__init__(**kwargs)

        self.spacing = 10
        self.orientation = 'vertical'

        self.add_widget(Label(text='Game flow control', size_hint_y = 0.2))
        self.start_game = Button(text='Start game')
        self.start_game.bind(on_press=self.do_start_game)
        self.add_widget(self.start_game)
        self.stop_game = Button(text='Stop game')
        self.stop_game.bind(on_press=self.do_end_game)
        self.add_widget(self.stop_game)
        self.do_setup = Button(text='debug setup (2)')
        self.do_setup.bind(on_press=self.do_debug_setup2)
        self.add_widget(self.do_setup)
        self.do_setup4 = Button(text='debug setup (4)')
        self.do_setup4.bind(on_press=self.do_debug_setup4)
        self.add_widget(self.do_setup4)
        self.remove_all = Button(text='remove players')
        self.remove_all.bind(on_press=self.do_remove_all)
        self.add_widget(self.remove_all)

        self.pause_unpause_timer = Button(text='(Un)Pause timer')
        self.pause_unpause_timer.bind(on_press=self.do_pause_unpause)
        self.add_widget(self.pause_unpause_timer)

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

class PlayerControl(BoxLayout):
    def __init__(self, **kwargs):
        super(PlayerControl, self).__init__(**kwargs)

        self.pid = kwargs['pid']
        self.spacing = 5
        self.orientation='vertical'

        self.add_widget(Label(text='{}'.format(self.pid), size_hint_y=0.2))
        self.incr_score = Button(text='+1')
        self.incr_score.bind(on_press=self.do_incr_score)
        self.add_widget(self.incr_score)
        self.decr_score = Button(text='-1')
        self.decr_score.bind(on_press=self.do_decr_score)
        self.add_widget(self.decr_score)
        self.force_serve = Button(text='F')
        self.force_serve.bind(on_press=self.do_force_serve)
        self.add_widget(self.force_serve)

    def do_incr_score(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/sincr/{}'.format(self.pid))

    def do_decr_score(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/sdecr/{}'.format(self.pid))

    def do_force_serve(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/pass')

class TestingControl(BoxLayout):
    def __init__(self, **kwargs):
        super(TestingControl, self).__init__(**kwargs)

        self.spacing = 10
        self.orientation = 'vertical'

        self.add_widget(Label(text='Testing & debugging', size_hint_y = 0.2))
        self.test_score_1 = Button(text='score 1 array test', size_hint_y = 0.7)
        self.test_score_1.bind(on_press=self.do_test_score_1)
        self.add_widget(self.test_score_1)

        self.test_score_2 = Button(text='score 2 array test', size_hint_y=0.7)
        self.test_score_2.bind(on_press=self.do_test_score_2)
        self.add_widget(self.test_score_2)

        self.test_score_3 = Button(text='score 3 array test', size_hint_y = 0.7)
        self.test_score_3.bind(on_press=self.do_test_score_3)
        self.add_widget(self.test_score_3)

        self.test_score_4 = Button(text='score 4 array test', size_hint_y = 0.7)
        self.test_score_4.bind(on_press=self.do_test_score_4)
        self.add_widget(self.test_score_4)

        #announcements
        self.announce = BoxLayout(spacing=5, orientation='vertical')
        self.announce.add_widget(Label(text='Announce', size_hint_y=0.5))
        self.ann_header = TextInput(multiline=False)
        self.ann_text  = TextInput(multiline=False)
        self.ann_put = Button(text='put')
        self.ann_put.bind(on_press=self.do_announce)

        self.announce.add_widget(self.ann_header)
        self.announce.add_widget(self.ann_text)
        self.announce.add_widget(self.ann_put)

        self.add_widget(self.announce)

        #play SFX
        self.sfx_play = BoxLayout(spacing=5, orientation='vertical', size_hint_y=0.8)
        self.sfx_play.add_widget(Label(text='SFX', size_hint_y=0.5))
        self.sfx_name = TextInput(multiline=False)
        self.sfx_start = Button(text='play')
        self.sfx_start.bind(on_press=self.do_sfx_play)

        self.sfx_play.add_widget(self.sfx_name)
        self.sfx_play.add_widget(self.sfx_start)

        self.add_widget(self.sfx_play)

    def do_sfx_play(self, * args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/sfx/{}'.format(self.sfx_name.text))

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
        heading = self.ann_header.text[:6]
        text = self.ann_text.text[:6]

        r = requests.get(SCOREBOARD_LOCATION+'/debug/announce/{},{},{}'.format(heading, text, 2))

class PlayerScoreSetter(BoxLayout):
    def __init__(self, **kwargs):
        super(PlayerScoreSetter, self).__init__(**kwargs)

        self.spacing = 5
        self.orientation = 'horizontal'

        self.pid = kwargs['playerNum']

        self.setter = BoxLayout(spacing=2, orientation='horizontal')
        self.score_input = TextInput(multiline=False)
        self.setter.add_widget(self.score_input)

        self.score_set = Button(text='set', size_hint_x=0.2)
        self.score_set.bind(on_press=self.do_set_score)
        self.setter.add_widget(self.score_set)

        self.add_widget(self.setter)

    def do_set_score(self, *args):

        try:
            score = int(self.score_input.text)
        except (TypeError, ValueError):
            print 'Invalid score input'
            return

        if score > 5 or score < -10:
            print 'Invalid score input'
            self.score_input.text = ''
            return

        r = requests.get(SCOREBOARD_LOCATION+'/debug/setscore/{},{}'.format(self.pid, score))

        try:
            response = r.json()
        except:
            return

        if response['status'] == 'error':
            print 'Could not set score, returned {}'.format(response['error'])


class GameDirectControl(BoxLayout):
    def __init__(self, **kwargs):
        super(GameDirectControl, self).__init__(**kwargs)

        self.spacing = 10
        self.orientation = 'vertical'
        self.add_widget(Label(text='Direct game control', size_hint_y = 0.2))

        for p in range(0,4):
            self.add_widget(Label(text='Player {} score'.format(p), size_hint_y=0.1))
            self.add_widget(PlayerScoreSetter(playerNum=p, size_hint_y=0.2))

        self.turn_setter = BoxLayout(spacing=5, orientation='vertical', size_hint_y=0.5)
        self.turn_setter.add_widget(Label(text='Set turn'))
        self.set_turn_0 = Button(text='0')
        self.set_turn_1 = Button(text='1')
        self.set_turn_2 = Button(text='2')
        self.set_turn_3 = Button(text='3')

        self.set_turn_0.bind(on_press=self.do_set_turn_1)
        self.set_turn_1.bind(on_press=self.do_set_turn_2)
        self.set_turn_2.bind(on_press=self.do_set_turn_3)
        self.set_turn_3.bind(on_press=self.do_set_turn_4)

        self.turn_setter.add_widget(self.set_turn_0)
        self.turn_setter.add_widget(self.set_turn_1)
        self.turn_setter.add_widget(self.set_turn_2)
        self.turn_setter.add_widget(self.set_turn_3)

        self.add_widget(self.turn_setter)


    def do_set_turn_1(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/setturn/0')

    def do_set_turn_2(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/setturn/1')

    def do_set_turn_3(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/setturn/2')

    def do_set_turn_4(self, *args):
        r = requests.get(SCOREBOARD_LOCATION+'/debug/setturn/3')

class PlayerInterfaceControl(BoxLayout):
    def __init__(self, **kwargs):
        super(PlayerInterfaceControl, self).__init__(**kwargs)

        self.padding = 5
        self.orientation = 'vertical'

        self.add_widget(Label(text='Indirect control', size_hint_y=0.2))
        self._box_3 = BoxLayout(padding=10, spacing=5, orientation='horizontal')
        for p in range(0,4):
            self._box_3.add_widget(PlayerControl(pid=p))
        self.add_widget(self._box_3)

class GameStatus(BoxLayout):
    def __init__(self, **kwargs):
        super(GameStatus, self).__init__(**kwargs)

        self.padding = 5
        self.orientation = 'vertical'

        self.add_widget(Label(text='Game status', size_hint_y = 0.2))
        self.status_label = Label(text='')
        self.add_widget(self.status_label)

        self.add_widget(Label(text='Game Timer', size_hint_y=0.2))
        self.timer_label = Label(text='00:00', size_hint_y=0.2)
        self.add_widget(self.timer_label)

        self.player_grid = BoxLayout(orientation='vertical')

        self.player_scores = []
        self.player_names = []
        self.player_0 = BoxLayout(orientation='horizontal')
        self.player_names.append(Label(text='',markup=True))
        self.player_scores.append(Label(text=''))
        self.player_0.add_widget(self.player_names[0])
        self.player_0.add_widget(self.player_scores[0])

        self.player_1 = BoxLayout(orientation='horizontal')
        self.player_names.append(Label(text='',markup=True))
        self.player_scores.append(Label(text=''))
        self.player_1.add_widget(self.player_names[1])
        self.player_1.add_widget(self.player_scores[1])

        self.player_2 = BoxLayout(orientation='horizontal')
        self.player_names.append(Label(text='',markup=True))
        self.player_scores.append(Label(text=''))
        self.player_2.add_widget(self.player_names[2])
        self.player_2.add_widget(self.player_scores[2])

        self.player_3 = BoxLayout(orientation='horizontal')
        self.player_names.append(Label(text='',markup=True))
        self.player_scores.append(Label(text=''))
        self.player_3.add_widget(self.player_names[3])
        self.player_3.add_widget(self.player_scores[3])

        self.player_grid.add_widget(self.player_0)
        self.player_grid.add_widget(self.player_1)
        self.player_grid.add_widget(self.player_2)
        self.player_grid.add_widget(self.player_3)
        self.add_widget(self.player_grid)

        Clock.schedule_interval(self.refresh_status, 1)

    def refresh_status(self, *args):

        r = requests.get(SCOREBOARD_LOCATION+'/status/all')
        status = r.json()

        #first look at board status
        json_data = status['board']
        if json_data['status'] == 'error':
            self.status_label.text = 'Scoreboard ERROR'
            return

        #get game status
        json_data = status['game']
        if json_data['status'] == 'error':
            self.status_label.text = 'Game ERROR'
            return

        server = -1
        if json_data['game'] == 'started':
            self.status_label.text = 'Game running'
            server = int(json_data['serving'])
        elif json_data['game'] == 'stopped':
            self.status_label.text = 'Game stopped'

        json_data = status['players']
        player_num = len(json_data)
        for i in range(0,4):
            if str(i) in json_data:
                self.player_names[i].text = json_data[str(i)]
            else:
                self.player_names[i].text = ''

        json_data = status['scores']
        if json_data['status'] == 'error':
            for i in range(0,4):
                self.player_scores[i].text = ''

        for i in range(0,4):
            if str(i) in json_data and i < player_num:
                self.player_scores[i].text = str(json_data[str(i)])
            else:
                self.player_scores[i].text = ''

        if server > -1:
            player_name = self.player_names[server].text
            self.player_names[server].text = '[color=ff0000]{}[/color]'.format(player_name)

        json_data = status['timer']
        if 'status' in json_data:
            if json_data['status'] == 'error':
                return

        self.timer_label.text ='{:0>2d}'.format(json_data['minutes']) + ':' + '{:0>2d}'.format(json_data['seconds'])

class ControlPanel(BoxLayout):

    def __init__(self, **kwargs):
        super(ControlPanel, self).__init__(**kwargs)
        self.padding = 10
        self.spacing = 10

        self.grid = GridLayout(cols=7)

        self.box_1 = BoxLayout(padding=10, orientation='horizontal')
        self.box_1.add_widget(FlowControl())
        self.grid.add_widget(self.box_1)

        self.box_2 = BoxLayout(padding=10, orientation='horizontal')
        self.box_2.add_widget(TestingControl())
        self.grid.add_widget(self.box_2)

        self.box_3 = BoxLayout(spacing=5, orientation='horizontal')
        self.box_3.add_widget(PlayerInterfaceControl())
        self.grid.add_widget(self.box_3)

        self.box_4 = BoxLayout(padding=10, orientation='horizontal')
        self.box_4.add_widget(GameDirectControl())
        self.grid.add_widget(self.box_4)

        self.box_5 = BoxLayout(padding=10, orientation='horizontal')
        self.box_5.add_widget(GameStatus())
        self.grid.add_widget(self.box_5)

        self.add_widget(self.grid)

class SimpleboardDebugPanel(App):

    def build(self):
        return ControlPanel()


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

    SimpleboardDebugPanel().run()
