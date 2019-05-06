from game.config import ChainballGameConfiguration
from game.persist import (
    PlayerPersistData,
    GamePersistData,
    CannotModifyScoresError,
    GamePersistance,
)

import os


class TestError(Exception):
    pass


def test_config():

    config = ChainballGameConfiguration()
    config.load_config(os.path.join("conf", "game.json"))

    # fail on purpose
    config.load_config("nonexistent_file")


def test_persist():

    p = PlayerPersistData(display_name="name", player_name="name")
    p.update_score(3)
    p.get_data()

    g = GamePersistData(players={0: p}, handler=None, current_series=0)
    g.assign_user_id("anid")

    try:
        g.update_score(player=1, score=0)
        raise TestError
    except KeyError:
        pass

    g.update_score(player=0, score=2, forced_update=False, game_time=300)
    g.update_score(player=0, score=1, forced_update=True, game_time=300)

    try:
        g.force_score(player=1, score=0)
        raise TestError
    except KeyError:
        pass

    g.force_score(player=0, score=0, game_time=300)
    g.start_game(remaining_time=1200)
    g.end_game(reason=None, winner=0, running_time=300, remaining_time=900)

    try:
        g.update_score(player=0, score=1)
        raise TestError
    except CannotModifyScoresError:
        pass

    try:
        g.force_score(player=0, score=1)
        raise
    except CannotModifyScoresError:
        pass

    g.start_game(remaining_time=1200)
    g.pause_unpause()
    g.pause_unpause()

    g.log_event(evt_type=None, evt_desc=None)
    g.to_JSON()

    # fail
    persist = GamePersistance("data/persist/game")

    # succeed
    persist = GamePersistance("data/persist/games")
    persist._test_mode = True

    persist.new_record({0: p})
    persist.log_event(evt_type=None, evt_desc=None)
    persist.start_game(remaining_time=1200)
    persist.end_game(reason=None, winner=0, running_time=300, remaining_time=900)
    persist.pause_unpause_game()
    persist.update_current_score(player=0, score=-1, forced_update=False, game_time=300)
    persist.force_current_score(player=0, score=0, game_time=300)
    persist.assign_user_id("id")
    persist.get_current_user_id()
