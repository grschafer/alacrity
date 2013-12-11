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
from collections import defaultdict
from utils import HeroNameDict, unitIdx
from parser import Parser, run_single_parser
from preparsers import GameStartTime

import traceback
import pdb

# structure:
# { building_hp:
#  { dota_good_towertop1:
#    { 90: 334.89,
#      80: 360.34,
#      ...
#    }, ...
#    OR
#    [{hp: 90, time: 334.89},
#     {hp: 80, time: 360.34},
#     ...
#    ]
#  },
# }
# access by: building_hp[building_type][building_name][threshold value] = time threshold crossed
# access by: building_hp[building_type][building_name] = {hp: threshold, time: crossed}

def hp_pct(e):
    try:
        return int(100.0 * e.health / e.max_health)
    except KeyError: # the entity is gone (died)
        return 0

class BuildingHpParser(Parser):
    def __init__(self, replay):
        self.gst = GameStartTime().results
        assert self.gst is not None
        self.building_hp = {b.properties[(u'DT_BaseEntity', u'm_iName')]:{}
                        for b in
                        replay.buildings.towers + replay.buildings.barracks + replay.buildings.ancients}

        self.game_buildings = {b.properties[(u'DT_BaseEntity', u'm_iName')]:b
                        for b in
                        replay.buildings.towers + replay.buildings.barracks + replay.buildings.ancients}

        # stores health from prev iteration (to test for falling below a threshold)
        self.building_prevhp = {b.properties[(u'DT_BaseEntity', u'm_iName')]:hp_pct(b)
                        for b in
                        replay.buildings.towers + replay.buildings.barracks + replay.buildings.ancients}

        self.thresholds = range(90, -1, -10)
        self.cur_hp = None

    @property
    def tick_step(self):
        return 150

    def parse(self, replay):
        if replay.info.pausing_team:
            return

        destroyed = []
        for name,b in self.game_buildings.iteritems():
            self.cur_hp = hp_pct(b)

            # mark building for removal from iteration list
            if self.cur_hp == 0:
                destroyed.append(name)

            # iterate all thresholds to account for building healing
            for thresh in self.thresholds:
                # if it fell below threshold since last tick iteration, store the time
                if self.cur_hp <= thresh < self.building_prevhp[name]:
                    self.building_hp[name][thresh] = (replay.info.game_time - self.gst)
            self.building_prevhp[name] = self.cur_hp

        for d in destroyed:
            del self.game_buildings[d]

    def end_game(self, replay):
        self.parse(replay)

        # transform last dict to a list sorted by time
        #   this makes it so the javascript doesn't need to know the threshold values,
        #   it can just iterate and check for the most recent time
        for name, threshtimes in self.building_hp.iteritems():
            self.building_hp[name] = sorted([{'hp': k, 'time': v} for k,v in threshtimes.iteritems()], key=lambda x: x['hp'], reverse=True)

    @property
    def results(self):
        return {'building_hp': self.building_hp}


def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    print 'match:', match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    hp = run_single_parser(BuildingHpParser, replay)
    print hp
    #with open('pos.out', 'w') as f:
    #    f.write(str(positions))
    match.update(hp)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
