#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from api import get_match_details
from db import db
from collections import defaultdict

import traceback
import pdb

def extract_positions(replay):
    pos = defaultdict(list)
    x = y = None
    #pdb.set_trace()
    for tick in replay.iter_ticks(start="pregame", end="postgame", step=30):
        if replay.info.pausing_team:
            continue
        for pl in replay.players:
            x,y = pl.hero.position if pl.hero else (0,0)
            pos[pl.hero.name].append((int(x),int(y)))
        pos['tick'].append(tick)

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
