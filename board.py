from game.engine import ChainballGame
from web import WebBoard
import threading
import logging
import time
import argparse
import signal

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

    logger.info("Scoreboard Starting")

    signal.signal(signal.SIGTERM, _handle_signal)

    #create game object
    game = ChainballGame(virtual_hw=args.nohw)

    #web server
    webScoreBoard = WebBoard(args.port, game, bind_all=True)

    #spawn web server
    web_server = threading.Thread(target=webScoreBoard.run)
    web_server.start()

    game.post_init()

    #never exit
    while True:
        try:
            game.game_loop()

            #throttle main loop
            time.sleep(0.01)
        except KeyboardInterrupt:
            game.shutdown()
            #webScoreBoard.quit()
            exit(0)
