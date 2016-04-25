from bottle import route, run, template, static_file, request
from game.playertxt import PlayerText
from game.exceptions import PlayerNotRegisteredError, TooManyPlayersError, PlayerAlreadyPairedError, PlayerNotPairedError, GameRunningError, NotEnoughPlayersError, GameNotStartedError, GameAlreadyStarterError, GameAlreadyPausedError, GameNotPausedError
import logging
from announce.timer import TimerAnnouncement
import time

class WebBoard(object):

    def __init__(self, port, game_handler, bind_all=True):

        self.port = port
        self.game = game_handler
        self.bind_all = bind_all
        self.logger = logging.getLogger('sboard.web')

    def quit(self):
        self.logger.debug('killing web server')
        exit(0)

    #views (templates)
    def index(self):
        return template('index', gameData=self.game)

    def setup(self):
        return template('psetup', gameData=self.game)

    def example(self):
        return template('base')

    def jsFiles(self, filename):
        return static_file(filename, root='data/web_static/js')

    def cssFiles(self, filename):
        return static_file(filename, root='data/web_static/css')

    def imgFiles(self, filename):
        return static_file(filename, root='data/web_static/images')

    def fontFiles(self, filename):
        return static_file(filename, root='data/web_static/fonts')

    def staticFiles(self, filename):
        return static_file(filename, root='data/web_static')

    def begin_game(self):
        try:
            self.game.game_begin()
        except (NotEnoughPlayersError, GameAlreadyStarterError) as e:
            self.logger.warning('Could not start game: {}'.format(e.message))
            return {'status' : 'error', 'error' : e.message}

        return {'status' : 'ok'}

    def end_game(self):
        try:
            self.game.game_end(reason='FORCED_STOP')
        except GameNotStartedError as e:
            self.logger.warning('Could not stop game: {}'.format(e.message))
            return {'status' : 'error', 'error' : e.message}

        return {'status' : 'ok'}

    #start pairing
    def pair(self):

        player = request.POST['playerNumber']

        if player == "master":
            try:
                self.game.pair_master()
            except:
                return 'Failed'
        else:
            try:
                self.game.pair_remote(int(player))
            except KeyError:
                return 'Invalid player!'
            except PlayerNotRegisteredError:
                return 'Player is not registered!'
            except PlayerAlreadyPairedError:
                return 'Player already paired to a remote'

        return 'Waiting'

    #unpair
    def unpair(self):

        player = request.POST['playerNumber']

        if player == "master":
            self.game.unpair_master()
        else:
            try:
                self.game.unpair_remote(int(player))
            except KeyError:
                return {'status' : 'error', 'error' : 'malformed request'}
            except (PlayerNotRegisteredError, PlayerNotPairedError) as e:
                return {'status' : 'error', 'error' : e.message}

        return {'status' : 'OK' }

    #get pairing status
    def is_pairing(self):
        status, reason = self.game.pair_running()
        if status == 'PAIR':
            return {'status': 'PAIR', 'text': 'Waiting for remote'}
        elif status == 'FAIL':
            if reason == RemotePairFailureType.TIMEOUT:
                reason_txt = 'Timed out'
            elif reason == RemotePairFailureType.ALREADY_PAIRED:
                reason_txt = 'Remote already paired to other player'
            else:
                reason_txt = 'Unknown error'
            return {'status': 'FAIL', 'text': 'Failed: {}'.format(reason_txt)}
        else:
            return {'status': 'OK', 'text': 'Success'}
        #return (self.game.pair_running())

    def register(self):

        #self.logger.debug('REGISTER')

        player_data = request.POST
        #self.logger.debug('DUMP: {}'.format([x for x in player_data]))
        try:
            player = self.game.next_player_num()
            self.game.register_players({player: PlayerText(player_data['panelTxt'],
                                                           player_data['webTxt'])})
        except TooManyPlayersError:
            self.logger.debug('Could not register player: too many players active')
            return {'status' : 'error', 'error' :'Cant register player'}
        except TypeError:
            return {'status' : 'error', 'error' :'Invalid player input'}
        except ValueError:
            self.logger.debug('Could not register player {}: invalid text'.format(player))
            return {'status' : 'error', 'error' : 'Invalid player texts'}
        except GameRunningError as e:
            return {'status' : 'error', 'error' : e.message}
        except KeyError:
            return {'status' : 'error', 'error' : 'Malformed request'}

        return {'status' : 'OK', 'playerNum' : player}

    def debug_setup(self):
        try:
            player = self.game.next_player_num()
            self.game.register_players({player: PlayerText('a', 'a')})
        except TooManyPlayersError:
            return {'status' :  'error', 'error' : 'too many players'}

        try:
            player = self.game.next_player_num()
            self.game.register_players({player: PlayerText('b', 'b')})
        except TooManyPlayersError:
            return {'status' : 'error', 'error' : 'too many players'}

        self.game.players[0].remote_id = 1
        self.game.players[1].remote_id = 2

        return {'status' : 'ok'}

    def unregister(self):

        player = request.POST['playerNumber']
        try:
            self.game.unregister_players([int(player)])
        except KeyError:
            return {'status' : 'error', 'error' : 'Invalid player'}
        except (GameRunningError, PlayerNotRegisteredError) as e:
            return {'status' : 'error', 'error' : e.message}

        return {'status' : 'ok'}

    def pmove(self):

        player = int(request.POST['playerNumber'])
        direction = request.POST['direction']

        if direction == 'up':
            other_player = player - 1
        elif direction == 'down':
            other_player = player + 1
        else:
            return 'Error'

        try:
            self.game.game_swap_players([player, other_player])
        except:
            raise

        return 'OK'

    def announce(self):

        heading = request.POST['heading']
        text = request.POST['text']
        duration = request.POST['duration']

        try:
            self.game.do_announcement(TimerAnnouncement(heading, text), int(duration))
        except TypeError:
            return {'status' : 'error', 'error' :  'malformed request'}

        return {'status' : 'ok'}

    def announce_debug(self, heading, text, duration):

        try:
            self.game.do_announcement(TimerAnnouncement(heading, text), int(duration))
        except TypeError:
            return {'status' : 'error', 'error' : 'malformed request'}
        return {'status' : 'ok'}

    def timeroff(self):
        self.game.timer_handler.poweroff_matrix()
        return {'status' : 'ok'}

    def timeron(self):
        self.game.timer_handler.poweron_matrix()
        return {'status' : 'ok'}

    def fpair(self, player, remote_id):
        try:
            self.game.players[int(player)].remote_id = int(remote_id)
        except TypeError:
            return {'status' : 'error', 'error' : 'malformed request'}

        return {'status' : 'ok'}

    def funpair(self, player):
        self.game.players[int(player)].remote_id = None

        return {'status' : 'ok'}

    def tpass(self):
        try:
            self.game.game_pass_turn()
        except GameNotStartedError as e:
            self.logger.warning('Could not pass turn: {}'.format(e.message))
            return {'status' : 'error', 'error' : e.message}

        return {'status' : 'ok'}

    def sscore(self, player):

        for i in range(-10, 6):
            self.game.s_handler.update_score(int(player), i)
            time.sleep(0.5)

    def set_score(self, player, score):
        try:
            self.game.players[int(player)].current_score = int(score)
        except KeyError:
            return {'status' : 'error', 'error' : 'Invalid player'}
        except TypeError:
            return {'status' : 'error', 'error' : 'Malformed request'}

        return {'status' : 'ok'}

    def play_sfx(self, fx):

        try:
            self.game.sfx_handler.play_fx(fx)
        except KeyError as e:
            self.logger.warning('Could not play SFX: {}'.format(e.message))
            return {'status' : 'error', 'error' : e.message}

        return {'status' : 'ok'}

    def incr_score(self, player):

        try:
            self.game.game_increment_score(int(player))
        except TypeError:
            return {'status' : 'error', 'error' : 'malformed request'}

        return {'status' : 'ok'}

    def decr_score(self, player):

        try:
            self.game.game_decrement_score(int(player))
        except TypeError:
            return {'status' : 'error', 'error' : 'malformed request'}

        return {'status' : 'ok'}

    def get_scores(self):

        score_dict = {'status' : 'ok'}

        if self.game.ongoing:

            for player in self.game.players:
                score_dict[str(player)] = self.game.players[player].current_score
        else:
            return {'status' : 'error'}

        return score_dict

    def core_status(self):

        if self.game.error:
            return {'status' : 'error'}

        return {'status' : 'ok'}

    def set_turn(self, player):

        try:
            p = int(player)
        except TypeError:
            return {'status' : 'error', 'error' : 'malformed request'}

        self.game.game_set_active_player(p)

        return {'status' : 'ok'}

    def get_players(self):

        players = {}
        for player in self.game.players:
            if self.game.players[player].registered:
                players[str(player)] = self.game.players[player].panel_text

        return players

    def get_timer(self):
        td = self.game.timer_handler.get_timer()

        if td == None:
            return {'status' : 'error', 'error' : 'game not running or not started'}

        if td.days < 0:
            minutes = 0
            seconds = 0
        else:
            hours, remainder = divmod(td.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

        return {'minutes' : minutes, 'seconds' : seconds}

    def get_game_status(self):

        if self.game.ongoing:
            return {'status' : 'ok', 'game' : 'started', 'serving' : self.game.active_player}
        else:
            return {'status' : 'ok', 'game' : 'stopped'}

    def pause_unpause(self):

        try:
            if self.game.paused:
                self.game.game_unpause()
            else:
                self.game.game_pause()
        except (GameNotStartedError, GameAlreadyPausedError, GameNotPausedError) as e:
            self.logger.warning('Could not pause/unpause game: {}'.format(e.message))
            return {'status' : 'error', 'error' : e.message}

        return {'status' : 'ok'}

    def get_all_status(self):
        timer = self.get_timer()
        board = self.core_status()
        game = self.get_game_status()
        players = self.get_players()
        scores = self.get_scores()

        return {'board' : board, 'game' : game,
                'players' : players, 'scores' : scores, 'timer' : timer}

    def run(self):

        #route
        route("/")(self.index)
        route("/index.html")(self.index)
        route("/setup")(self.setup)
        route("/js/<filename:re:.*\.js>")(self.jsFiles)
        route("/css/<filename:re:.*\.css>")(self.cssFiles)
        route("/images/<filename:re:.*\.(jpg|png|gif|ico)>")(self.imgFiles)
        route("/fonts/<filename:re:.*\.(eot|ttf|woff|svg)>")(self.fontFiles)

        #control
        route("/control/gbegin")(self.begin_game)
        route("/control/gend")(self.end_game)
        route("/control/rpair", method="POST")(self.pair)
        route("/control/runpair", method="POST")(self.unpair)
        route("/control/pregister", method="POST")(self.register)
        route("/control/punregister", method="POST")(self.unregister)
        route("/control/pmove", method="POST")(self.pmove)
        route("/control/announce", method="POST")(self.announce)
        route("/control/pauseunpause")(self.pause_unpause)

        #development
        #route("/example")(self.example)
        route("/debug/announce/<heading>,<text>,<duration>")(self.announce_debug)
        route("/debug/timeroff")(self.timeroff)
        route("/debug/timeron")(self.timeron)
        route("/debug/fpair/<player>,<remote_id>")(self.fpair)
        route("/debug/funpair/<player>")(self.funpair)
        route("/debug/pass")(self.tpass)
        route("/debug/scoretest/<player>")(self.sscore)
        route("/debug/setscore/<player>,<score>")(self.set_score)
        route("/debug/sfx/<fx>")(self.play_sfx)
        route("/debug/sincr/<player>")(self.incr_score)
        route("/debug/sdecr/<player>")(self.decr_score)
        route("/debug/psetup")(self.debug_setup)
        route("/debug/setturn/<player>")(self.set_turn)


        #information channels
        route("/status/pairing")(self.is_pairing)
        route("/status/scores")(self.get_scores)
        route("/status/board")(self.core_status)
        route("/status/players")(self.get_players)
        route("/status/timer")(self.get_timer)
        route("/status/game")(self.get_game_status)
        route("/status/all")(self.get_all_status)

        if self.bind_all:
            bind_to = '0.0.0.0'
        else:
            bind_to = '127.0.0.1'

        run(host=bind_to, port=self.port)
