#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from api import get_match_details
from db import db
from collections import defaultdict
from utils import HeroNameDict, unitIdx

import traceback
import pdb

# structure:
# { building_hp:
#   { towers:
#     { dota_good_towertop1:
#       { 90: 334.89,
#         80: 360.34,
#         ...
#       }, ...
#       OR
#       [{hp: 90, time: 334.89},
#        {hp: 80, time: 360.34},
#        ...
#       ]
#     },
#     rax:
#     { ...
#     },
#     ancients: ...
#   }
# }
# access by: building_hp[building_type][building_name][threshold value] = time threshold crossed
# access by: building_hp[building_type][building_name] = {hp: threshold, time: crossed}

# todo: profile this b/c it gets called so much
def hp_pct(e):
    try:
        return float(e.health) / e.max_health
    except KeyError: # the entity is gone (died)
        return 0

def extract_hp(replay):
    tower_hp = {b.properties[(u'DT_BaseEntity', u'm_iName')]:{} for b in replay.buildings.towers}
    rax_hp = {b.properties[(u'DT_BaseEntity', u'm_iName')]:{} for b in replay.buildings.barracks}
    ancient_hp = {b.properties[(u'DT_BaseEntity', u'm_iName')]:{} for b in replay.buildings.ancients}

    game_towers = {b.properties[(u'DT_BaseEntity', u'm_iName')]:b for b in replay.buildings.towers}
    game_rax = {b.properties[(u'DT_BaseEntity', u'm_iName')]:b for b in replay.buildings.barracks}
    game_ancients = {b.properties[(u'DT_BaseEntity', u'm_iName')]:b for b in replay.buildings.ancients}

    # stores health from prev iteration (to test for falling below a threshold)
    tower_prevhp = {b.properties[(u'DT_BaseEntity', u'm_iName')]:hp_pct(b) for b in replay.buildings.towers}
    rax_prevhp = {b.properties[(u'DT_BaseEntity', u'm_iName')]:hp_pct(b) for b in replay.buildings.barracks}
    ancient_prevhp = {b.properties[(u'DT_BaseEntity', u'm_iName')]:hp_pct(b) for b in replay.buildings.ancients}

    thresholds = range(90, -1, -10)
    cur_hp = None

    for tick in replay.iter_ticks(start="pregame", end="postgame", step=150):
        if replay.info.pausing_team:
            continue

        # TODO: all the following code is the same, REFACTOR
        # towers
        for name,b in game_towers.iteritems():
            cur_hp = hp_pct(b)
            # iterate all thresholds to account for building healing
            for thresh in thresholds:
                # if it fell below threshold since last tick iteration, store the time
                if cur_hp <= thresh < tower_prevhp[name]:
                    tower_hp[name][thresh] = replay.info.game_time
            tower_prevhp[name] = cur_hp

        # barracks
        for name,b in game_rax.iteritems():
            cur_hp = hp_pct(b)
            for thresh in thresholds:
                if cur_hp <= thresh < rax_prevhp[name]:
                    rax_hp[name][thresh] = replay.info.game_time
            rax_prevhp[name] = cur_hp

        # ancients
        for name,b in game_ancients.iteritems():
            cur_hp = hp_pct(b)
            for thresh in thresholds:
                if cur_hp <= thresh < ancient_prevhp[name]:
                    ancient_hp[name][thresh] = replay.info.game_time
            ancient_prevhp[name] = cur_hp

    # transform last dict to a list sorted by time
    #   this makes it so the javascript doesn't need to know the threshold values,
    #   it can just iterate and check for the most recent time
    for name, threshtimes in tower_hp.iterkeys():
        tower_hp[name] = sorted([{'hp': k, 'time': v} for k,v in threshtimes.iteritems()], key=lambda x: x['time'])
    for name, threshtimes in rax_hp.iterkeys():
        rax_hp[name] = sorted([{'hp': k, 'time': v} for k,v in threshtimes.iteritems()], key=lambda x: x['time'])
    for name, threshtimes in ancient_hp.iterkeys():
        ancient_hp[name] = sorted([{'hp': k, 'time': v} for k,v in threshtimes.iteritems()], key=lambda x: x['time'])

    return {'building_hp':{'towers':tower_hp, 'rax':rax_hp, 'ancients':ancient_hp}}

def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    positions = extract_positions(replay)
    print positions
    #with open('pos.out', 'w') as f:
    #    f.write(str(positions))
    match.update(positions)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
