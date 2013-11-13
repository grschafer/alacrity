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

import traceback
import pdb

gst = None # game_start_time
def extract_positions(replay):
    pos = defaultdict(list)
    x = y = None
    name = None
    #pdb.set_trace()

    replay.go_to_tick('postgame')
    global gst
    gst = replay.info.game_start_time
    player_hero_map = {p.index:HeroNameDict[unitIdx(p.hero)]['name'] for p in replay.players}

    for tick in replay.iter_ticks(start="pregame", end="postgame", step=30):
        if replay.info.pausing_team:
            continue
        for pl in replay.players:
            if pl:
                name = player_hero_map[pl.index]
                x,y = pl.hero.position if pl.hero else (0,0)
                hp_pct = int(float(pl.hero.health) / pl.hero.max_health * 100)
                pos[name].append((int(x),int(y),hp_pct))
        pos['time'].append(replay.info.game_time - gst)

    return {'positions':dict(pos)}

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