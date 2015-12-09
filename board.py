from game.engine import ChainballGame
from web import WebBoard
import threading
import logging
import time
import argparse

if __name__ == "__main__":

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

    #create game object
    game = ChainballGame(virtual_hw=args.nohw)

    #web server
    webScoreBoard = WebBoard(args.port, game, bind_all=True)

    #spawn web server
    threading.Thread(target=webScoreBoard.run).start()

    game.post_init()

    #never exit
    while True:
        game.game_loop()

        #throttle main loop
        time.sleep(0.01)
