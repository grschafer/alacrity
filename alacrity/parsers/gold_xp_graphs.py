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


import pdb
import traceback
from collections import defaultdict

gst = None # game_start_time
def extract_graphs(replay):
    xp_dict = defaultdict(list)
    gold_dict = defaultdict(list)
    xp = None
    gold = None
    name = None

    replay.go_to_tick('postgame')
    global gst
    gst = replay.info.game_start_time
    player_hero_map = {p.index:HeroNameDict[unitIdx(p.hero)]['name'] for p in replay.players}

    for tick in replay.iter_ticks(start="pregame", end="postgame", step=300):
        if replay.info.pausing_team:
            continue
        xp_dict['time'].append(replay.info.game_time - gst)
        gold_dict['time'].append(replay.info.game_time - gst)
        for player in replay.players:
            name = player_hero_map[player.index]
            xp = player.hero.xp if player.hero else 0
            xp_dict[name].append(xp)
            gold = player.earned_gold
            gold_dict[name].append(gold)

    return {'xp_graph':dict(xp_dict), 'gold_graph':dict(gold_dict)}

def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    xp, gold = extract_graphs(replay)
    #dict_to_csv('xp.csv', xp)
    #dict_to_csv('gold.csv', gold)
    #match['wards'] = wards
    match.update(xp)
    match.update(gold)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()