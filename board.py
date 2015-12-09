from game.engine import ChainballGame
from web import WebBoard
import threading
import logging
import time

NO_HW = False
BIND_TO_ALL = True
WEB_PORT = 80

#NO_HW = True
#BIND_TO_ALL = True
#WEB_PORT = 8080

if __name__ == "__main__":

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
    game = ChainballGame(virtual_hw=NO_HW)

    #web server
    webScoreBoard = WebBoard(WEB_PORT, game, bind_all=BIND_TO_ALL)

    #spawn web server
    threading.Thread(target=webScoreBoard.run).start()

    game.post_init()

    #never exit
    while True:
        game.game_loop()

        #throttle main loop
        time.sleep(0.01)
