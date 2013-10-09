#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from api import get_match_details
from db import db
from inspect_props import dict_to_csv
from utils import HeroNameDict, unitIdx


import traceback
from collections import defaultdict

def buyback_cost(player, game_info):
    level = player.hero.level
    # convert time from seconds to minutes
    # NOT CONFIDENT ABOUT SUBTRACTING 90
    game_time = (game_info.game_time - 90) / 60.
    raw = 100 + (level*level*1.5) + (game_time * 15)
    return int(raw / 50) * 50

# look in user_messages for chat_event type=7, buyback by player
def extract_buybacks(replay):
    bbs = []
    bb_cost = None
    name = None

    replay.go_to_tick('postgame')
    player_hero_map = {p.index:HeroNameDict[unitIdx(p.hero)]['name'] for p in replay.players}

    for tick in replay.iter_ticks(start="pregame", end="postgame", step=30):
        #print 'tick: {}'.format(tick)
        msgs = replay.user_messages
        buybacks = [x[1] for x in msgs if x[0] == 66 and x[1].type == 7]
        for msg in buybacks:
            bb_cost = buyback_cost([p for p in replay.players if p.index == msg.playerid_1][0], replay.info)
            name = player_hero_map[msg.playerid_1]
            bbs.append({'tick':tick, 'cost':bb_cost, 'hero':name})
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
