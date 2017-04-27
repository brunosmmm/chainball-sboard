from game.engine import ChainballGame
from web import WebBoard
import threading
import logging
import time
import argparse
import signal
from util.threads import StoppableThread
from util.zeroconf import ZeroconfService

if __name__ == "__main__":

    def _handle_signal(*args):
        exit(0)

    parser = argparse.ArgumentParser()
    parser.add_argument('--nohw', action='store_true', help='hardware not present, development only')
    parser.add_argument('--port', help='web interface port', default=80)

    args = parser.parse_args()

    #main loop
    logging.basicConfig(level=logging.DEBUG,
                        filename='scoreboard.log',
                        filemode='w',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)

    logger = logging.getLogger('sboard')

    #publish
    avahi_service = ZeroconfService(name='Chainball Scoreboard',
                                    port=args.port,
                                    stype='_http._tcp')
    avahi_service.publish()

    logger.info("Scoreboard Starting")

    signal.signal(signal.SIGTERM, _handle_signal)

    class GameWrapper(StoppableThread):

        def __init__(self, virtual_hw):
            super(GameWrapper, self).__init__()
            #create game object
            self.game = ChainballGame(virtual_hw=virtual_hw)
            self.game.post_init()

        def run(self):
            #never exit
            while True:
                if self.is_stopped():
                    self.game.shutdown()
                    break
                else:
                    self.game.game_loop()

                    #throttle main loop
                    time.sleep(0.01)

    #spawn game engine in thread
    game_wrapper = GameWrapper(args.nohw)
    game_wrapper.start()

    #web server
    # NOT THREAD SAFE
    webScoreBoard = WebBoard(args.port, game_wrapper.game, bind_all=True)

    #spawn web server
    webScoreBoard.run()
    #web_server = threading.Thread(target=webScoreBoard.run)
    #web_server.daemon = True
    #web_server.start()

    game_wrapper.stop()
    avahi_service.unpublish()
