#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from api import get_match_details
from db import db

import traceback
import pdb

def extract_positions(replay):
    pos = [[] for i in range(10)]
    x = y = None
    pdb.set_trace()
    for tick in replay.iter_ticks(start="pregame", step=30):
        for pl in replay.players:
            if pl.hero:
                x,y = pl.hero.position
                pos[pl.index].append((int(x),int(y)))

    return pos

def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    positions = extract_positions(replay)
    print positions
    pdb.set_trace()
    with open('pos.out', 'w') as f:
        f.write(str(positions))
    #match['positions'] = positions
    #result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
