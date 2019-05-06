"""Chainball Game."""

from game.engine import ChainballGame
from web import WebBoard
import logging
import time
import argparse
import signal
from util.threads import StoppableThread
from util.zeroconf import ZeroconfService

if __name__ == "__main__":

    def _handle_signal(*args):
        exit(0)

    # Parse Command Line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--nohw", action="store_true", help="hardware not present, development only"
    )
    parser.add_argument("--port", help="web interface port", default=80)

    args = parser.parse_args()

    # main loop
    logging.basicConfig(
        level=logging.DEBUG,
        filename="scoreboard.log",
        filemode="w",
        format="%(asctime)s - %(name)s -" " %(levelname)s - %(message)s",
    )

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger("").addHandler(console)

    logger = logging.getLogger("sboard")

    # publish as service
    published = False
    try:
        avahi_service = ZeroconfService(
            name="Chainball Scoreboard", port=args.port, stype="_http._tcp"
        )
        avahi_service.publish()
        published = True
    except Exception as ex:
        logger.error("failed to publish scoreboard service: {}".format(ex))

    logger.info("Scoreboard Starting")

    signal.signal(signal.SIGTERM, _handle_signal)

    class GameWrapper(StoppableThread):
        """Main Game Thread."""

        def __init__(self, virtual_hw):
            """Initialize."""
            super(GameWrapper, self).__init__()
            # create game object
            self.game = ChainballGame(virtual_hw=virtual_hw)
            self.game.post_init()

        def run(self):
            """Run thread."""
            # never exit
            while True:
                if self.is_stopped():
                    self.game.shutdown()
                    break
                else:
                    self.game.game_loop()

                    # throttle main loop
                    time.sleep(0.01)

    # spawn game engine in thread
    game_wrapper = GameWrapper(args.nohw)
    game_wrapper.start()

    # web server
    # NOT THREAD SAFE
    webScoreBoard = WebBoard(args.port, game_wrapper.game, bind_all=True)

    # spawn web server
    webScoreBoard.run()

    # done, cleanup and exit
    game_wrapper.stop()
    if published:
        avahi_service.unpublish()
