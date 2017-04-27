from bottle import route, run, template, static_file, request, response, Response, HeaderDict, default_app, ServerAdapter
from game.playertxt import PlayerText
from game.exceptions import PlayerNotRegisteredError, TooManyPlayersError, PlayerAlreadyPairedError, PlayerNotPairedError, GameRunningError, NotEnoughPlayersError, GameNotStartedError, GameAlreadyStarterError, GameAlreadyPausedError, GameNotPausedError, PlayerRemoteNotPaired
import logging
from game.persist import GamePersistData
from announce.timer import TimerAnnouncement
from remote.persistence import PERSISTENT_REMOTE_DATA
import time
import json

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
        except (NotEnoughPlayersError,
                GameAlreadyStarterError,
                PlayerNotPairedError,
                PlayerRemoteNotPaired) as e:
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
            if 'playerNum' not in player_data:
                player = self.game.next_player_num()
            else:
                player = int(player_data['playerNum'])
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

    def assign_uid(self):
        uid_data = request.POST

        if 'game_id' not in uid_data:
            return {'status': 'error', 'error': 'missing game id'}

        if 'user_id' not in uid_data:
            return {'status': 'error', 'error': 'missing user id'}

        try:
            self.game.g_persist.assign_user_id(uid_data['user_id'])
        except Exception as ex:
            return {'status': 'error', 'error': 'internal error'}

        return {'status': 'ok'}

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
            self.game.game_pass_turn(force_serve=True)
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
            self.game.game_force_score(int(player),
                                       int(score))
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

    def _get_scores(self):
        score_dict = {}
        if self.game.ongoing:
            for player in self.game.players:
                score_dict[str(player)] = self.game.players[player].current_score

        return score_dict

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
                player_dict = {}
                player_dict['panel_txt'] = self.game.players[player].panel_text
                player_dict['web_txt'] = self.game.players[player].web_text
                player_dict['remote_id'] = self.game.players[player].remote_id
                players[str(player)] = player_dict

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
            if self.game.paused:
                return {'status': 'ok',
                        'game': 'paused',
                        'game_id' : self.game.g_persist.current_game_series,
                        'user_id' : self.game.g_persist.get_current_user_id(),
                        'scores': self._get_scores()}
            return {'status' : 'ok',
                    'game' : 'started',
                    'serving' : self.game.active_player,
                    'game_id' : self.game.g_persist.current_game_series,
                    'user_id' : self.game.g_persist.get_current_user_id(),
                    'scores': self._get_scores()}
        else:
            return {'status' : 'ok',
                    'game' : 'stopped',
                    'game_id' : self.game.g_persist.current_game_series,
                    'user_id' : self.game.g_persist.get_current_user_id()}

    def pause_unpause(self):

        try:
            if self.game.paused:
                self.game.game_unpause()
            else:
                self.game.game_pause()
        except (GameNotStartedError,
                GameAlreadyPausedError,
                GameNotPausedError,
                PlayerRemoteNotPaired) as e:
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

    def get_persist_list(self):

        game_list = []
        game_list = self.game.g_persist.game_history.keys()

        return {'game_list': game_list}

    def dump_game_data(self, game_uuid):

        if game_uuid not in self.game.g_persist.game_history:
            return {'status': 'error',
                    'error': 'invalid uuid'}
        game_data = self.game.g_persist.game_history[game_uuid]
        if isinstance(game_data, GamePersistData):
            game_data = game_data.to_JSON()
        return {'status': 'ok',
                'data': game_data}

    def dump_game_readable(self, game_uuid):

        game_data = self.dump_game_data(game_uuid)

        if game_data['status'] == 'error':
            return 'ERROR'
        game_data = game_data['data']

        user_id = game_data['game_data']['user_id']
        player_data = game_data['player_data']
        event_list = game_data['events']

        #prevent exceptions
        try:
            ret = template('dump',
                           player_data=player_data,
                           event_list=event_list,
                           internal_id=game_uuid,
                           user_game_id=user_id,
                           evt_info_gen=self.generate_event_info_field)
        except Exception as ex:
            self.logger.error('Caught exception in dump_game_readable: {}'.format(repr(ex)))
            return Response('An error occured while processing this request', status=500)

        return ret

    def dump_game_range(self, start_uuid, count):
        #dump a csv representation

        def uuid_from_int(uuid):
            return '{0:06d}'.format(uuid)

        def timestamp_from_seconds(seconds):
            return '{:02d}:{:02d}'.format(seconds/60, seconds%60)

        # TODO: there are a lot of inconsistencies between player id, using both string
        # and integers
        def get_event_player(event, game):
            if 'player' in event['evt_desc']:
                id = event['evt_desc']['player']
                return game['player_data'][str(id)]['display_name']
            else:
                return '-'

        if start_uuid not in self.game.g_persist.game_history:
            return Response(body='Game Identifier ID not found', status=500)

        #check range

        if uuid_from_int(int(start_uuid) + int(count) - 1) not in self.game.g_persist.game_history:
            response.status = 500
            return 'ERROR: Provided range is out of bounds'

        #dump
        game_dumps = []
        for uuid in range(int(start_uuid), int(start_uuid)+int(count)):
            game_dump = []

            #re-use json data for consistency between dump modes
            game_info = self.dump_game_data(uuid_from_int(uuid))['data']

            #manually construct a bunch of lists
            game_dump.append(['GAME_INFO'])
            game_dump.append(['INTERNAL_GAME_ID', 'USER_GAME_ID'])
            game_dump.append([uuid, game_info['game_data']['user_id']])
            # first "table"
            game_dump.append(['PLAYER_LIST'])
            game_dump.append(['PLAYER_ID', 'PLAYER_NAME', 'PLAYER_SCORE'])
            # dump player info
            for player_id, player_data in sorted(game_info['player_data'].iteritems()):
                game_dump.append([str(int(player_id)+1),
                                  player_data['display_name'],
                                  player_data['score']])
            # second table
            game_dump.append(['EVENT_LIST'])
            game_dump.append(['EVENT_TYPE', 'EVENT_TIMESTAMP', 'EVENT_PLAYER', 'EVENT_INFO'])
            game_end_rtime = None
            for event in game_info['events']:
                if event['evt_type'] == 'GAME_END':
                    #store remaining time
                    game_end_rtime = event['evt_desc']['rtime']

                game_dump.append([event['evt_type'],
                                  timestamp_from_seconds(event['evt_desc']['gtime']),
                                  get_event_player(event, game_info),
                                  self.generate_event_info_field(event)])

            #dump miscellaneous
            game_dump.append(['MISC'])
            if game_end_rtime is not None:
                game_dump.append(['FINAL_CLOCK'])
                game_dump.append([timestamp_from_seconds(game_end_rtime)])

            #add everything together
            game_dumps.extend(game_dump)

        #make one big csv file
        csv_lines = [','.join([str(y) for y in x]) for x in game_dumps]
        csv_all = '\n'.join(csv_lines)

        #headers = {}
        response.headers['Content-Type'] = 'text/csv; charset=UTF-8'
        response.headers['Content-Disposition'] = 'attachment; '\
                                                  'filename=cbot_dump_{}_{}.csv'.format(start_uuid,
                                                                                        uuid_from_int(int(start_uuid)+int(count)))

        return csv_all

    def dump_fmt(self):

        ret = None
        with open('conf/game_dump_fmt.json', 'r') as f:
            ret = {}
            ret['fmt'] = json.load(f)
            ret['status'] = 'ok'

        if ret is None:
            return {'status': 'error'}

        return ret

    def score_evt(self, player, evt_type):
        self.game.scoring_evt(player, evt_type)

    def get_sfx_list(self):
        return {'status': 'ok',
                'sfx_list': self.game.sfx_handler.get_available_sfx()}

    def get_remote_data(self):
        return {'status': 'ok',
                'remote_data': PERSISTENT_REMOTE_DATA.get_remote_persist()}

    def generate_event_info_field(self, event):

        if 'evt_desc' not in event:
            raise KeyError('not valid')

        event_type = event['evt_type']
        event_desc = event['evt_desc']

        if event_type in ('SCORE_FORCED', 'SCORE_CHANGE'):
            #information is score delta
            ret = 'OLD = {}; NEW = {} ({:+d})'.format(event_desc['old_score'],
                                                      event_desc['new_score'],
                                                      event_desc['new_score']-event_desc['old_score'])
        elif event_type == 'GAME_END':
            ret = event_desc['reason']
        else:
            ret = '-'

        return ret

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
        route('/control/scoreevt/<player>,<evt_type>')(self.score_evt)

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
        route('/status/sfxlist')(self.get_sfx_list)
        route('/status/remotedata')(self.get_remote_data)

        #persistance
        route('/persist/game_list')(self.get_persist_list)
        route('/persist/dump_raw/<game_uuid>')(self.dump_game_data)
        route('/persist/dump_game/<game_uuid>')(self.dump_game_readable)
        route('/persist/dump_range/<start_uuid>,<count>')(self.dump_game_range)
        route('/persist/dump_fmt')(self.dump_fmt)
        route('/persist/assign_uid', method="POST")(self.assign_uid)

        if self.bind_all:
            bind_to = '0.0.0.0'
        else:
            bind_to = '127.0.0.1'

        #better server
        run(host=bind_to, port=self.port, server='cherrypy')
