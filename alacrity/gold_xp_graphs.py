#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from api import get_match_details
from db import db
from inspect_props import dict_to_csv


import pdb
import traceback
from collections import defaultdict
def extract_graphs(replay):
    xp_dict = defaultdict(list)
    gold_dict = defaultdict(list)
    xp = None
    gold = None

    replay.go_to_tick('postgame')
    player_hero_map = {p.index:p.hero.name for p in replay.players}

    for tick in replay.iter_ticks(start="pregame", step=300):
        if replay.info.pausing_team:
            continue
        xp_dict['tick'].append(tick)
        gold_dict['tick'].append(tick)
        for player in replay.players:
            xp = player.hero.xp if player.hero else 0
            xp_dict[player_hero_map[player.index]].append(xp)
            gold = player.earned_gold
            gold_dict[player_hero_map[player.index]].append(gold)

    return {'xp_graph':dict(xp_dict)}, {'gold_graph':dict(gold_dict)}

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
