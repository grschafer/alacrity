#!/usr/bin/python
# -*- coding: utf-8 -*-

# boilerplate to allow running as script directly
# http://stackoverflow.com/a/6655098/751774
if __name__ == "__main__" and __package__ is None:
    import sys, os
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    while os.path.exists(os.path.join(parent_dir, '__init__.py')):
        parent_dir = os.path.dirname(parent_dir)
        sys.path.insert(1, parent_dir)
    import alacrity.parsers
    __package__ = "alacrity.parsers"
    del sys, os

from tarrasque import *
import sys
from ..config.api import get_match_details
from ..config.db import db
from inspect_props import dict_to_csv
from utils import HeroNameDict, unitIdx


import traceback
from collections import defaultdict

def buyback_cost(player, replay):
    level = player.hero.level
    # convert time from seconds to minutes
    game_time = (replay.info.game_time - gst) / 60.
    raw = 100 + (level*level*1.5) + (game_time * 15)
    return int(raw)

# look in user_messages for chat_event type=7, buyback by player
gst = None # game_start_time
def extract_buybacks(replay):
    bbs = []
    bb_cost = None
    name = None

    replay.go_to_tick('postgame')
    global gst
    gst = replay.info.game_start_time
    player_hero_map = {p.index:HeroNameDict[unitIdx(p.hero)]['name'] for p in replay.players}

    for tick in replay.iter_ticks(start="pregame", end="postgame", step=30):
        #print 'tick: {}'.format(tick)
        if replay.info.pausing_team:
            continue
        msgs = replay.user_messages
        buybacks = [x[1] for x in msgs if x[0] == 66 and x[1].type == 7]
        for msg in buybacks:
            pl = [p for p in replay.players if p.index == msg.playerid_1][0]
            bb_cost = buyback_cost(pl, replay)
            name = player_hero_map[msg.playerid_1]
            bbs.append({'time':(replay.info.game_time - gst), 'event':'buyback', 'cost':bb_cost, 'hero':name})
    return {'buybacks':bbs}


def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    bbs = extract_buybacks(replay)
    print bbs
    match.update(bbs)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()