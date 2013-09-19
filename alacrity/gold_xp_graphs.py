#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from api import get_match_details
from db import db
from inspect_props import dict_to_csv


import traceback
from collections import defaultdict
def extract_graphs(replay):
    xp_dict = defaultdict(list)
    gold_dict = defaultdict(list)
    player_hero_map = {}
    heroes_assigned = False
    xp = None
    gold = None
    for tick in replay.iter_ticks(start="pregame", step=1500):
        xp_dict['tick'].append(tick)
        gold_dict['tick'].append(tick)
        for player in replay.players:
            xp = player.hero.xp if player.hero else 0
            xp_dict[player.name].append(xp)
            gold = player.earned_gold
            gold_dict[player.name].append(gold)

        if not heroes_assigned and replay.info.game_state == 'game':
            for player in replay.players:
                player_hero_map[player.name] = player.hero.name
            heroes_assigned = True

    try:
        for player in xp_dict.iterkeys():
            xp_dict[player].insert(0, player_hero_map.get(player, ''))
        for player in gold_dict.iterkeys():
            gold_dict[player].insert(0, player_hero_map.get(player, ''))
    except Exception:
        print traceback.format_exc()
        import pdb; pdb.set_trace()
        print 'test'
    return xp_dict, gold_dict

def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    xp, gold = extract_graphs(replay)
    dict_to_csv('xp.csv', xp)
    dict_to_csv('gold.csv', gold)
    #match['wards'] = wards
    #result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
