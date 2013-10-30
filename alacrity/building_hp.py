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

def hp_pct(e):
    try:
        return 100.0 * e.health / e.max_health
    except KeyError: # the entity is gone (died)
        return 0

def extract_hp(replay):
    building_hp = {b.properties[(u'DT_BaseEntity', u'm_iName')]:{}
                    for b in
                    replay.buildings.towers + replay.buildings.barracks + replay.buildings.ancients}

    game_buildings = {b.properties[(u'DT_BaseEntity', u'm_iName')]:b
                    for b in
                    replay.buildings.towers + replay.buildings.barracks + replay.buildings.ancients}

    # stores health from prev iteration (to test for falling below a threshold)
    building_prevhp = {b.properties[(u'DT_BaseEntity', u'm_iName')]:hp_pct(b)
                    for b in
                    replay.buildings.towers + replay.buildings.barracks + replay.buildings.ancients}

    thresholds = range(90, -1, -10)
    cur_hp = None

    for tick in replay.iter_ticks(start="pregame", end="postgame", step=150):
        if replay.info.pausing_team:
            continue

        destroyed = []
        for name,b in game_buildings.iteritems():
            cur_hp = hp_pct(b)

            # mark building for removal from iteration list
            if cur_hp == 0:
                destroyed.append(name)

            # iterate all thresholds to account for building healing
            for thresh in thresholds:
                # if it fell below threshold since last tick iteration, store the time
                if cur_hp <= thresh < building_prevhp[name]:
                    print name, thresh
                    building_hp[name][thresh] = replay.info.game_time
            building_prevhp[name] = cur_hp

        for d in destroyed:
            print 'removing', d
            del game_buildings[d]

    print building_hp
    # transform last dict to a list sorted by time
    #   this makes it so the javascript doesn't need to know the threshold values,
    #   it can just iterate and check for the most recent time
    for name, threshtimes in building_hp.iteritems():
        building_hp[name] = sorted([{'hp': k, 'time': v} for k,v in threshtimes.iteritems()], key=lambda x: x['time'])

    return {'building_hp': building_hp}

def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    print 'match:', match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    hp = extract_hp(replay)
    print hp
    #with open('pos.out', 'w') as f:
    #    f.write(str(positions))
    match.update(hp)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
