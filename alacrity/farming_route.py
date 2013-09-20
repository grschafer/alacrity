#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from api import get_match_details
from db import db

import traceback
import pdb

# NEXT IDEAS
#  courier kills
#  mouse clicks and mouse travel distance
#  "possession"
#  bonus gold/xp from midas/devour/track?

# CALL THIS "BEST 2-MINUTE CREEP GPM" instead of farming route?
def extract_routes(replay):
    top_farmers = []
    replay.go_to_tick('postgame')
    top_farmers = sorted(replay.players, key=lambda x: x.earned_gold / replay.info.game_end_time)[:4]

    pdb.set_trace()
    for tick in replay.iter_ticks(start="game", step=30):
        for pl in top_farmers:
            if pl.hero:
                x,y = pl.hero.position
                pos[pl.index].append((int(x),int(y)))

    # a queue of 2 minutes of {tick,x,y,earned_gold?} for each farmer
    # if combatlog contains 'farmer killed x' for x not a Creep_Lane/Creep_Neutral (convert raw names I guess), then flush queue
    #   this doesn't exclude tower kills, kill assists
    # MAYBE: if there is a gold overhead for farmer and not a corresponding last-hit count increase, then flush queue
    #   building kills go toward last hit count
    # each tick, if queue is full take max(existing_max, 2min_gpm) and if this is new max then deepcopy it
    # and push/pop current queue

    return pos

def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    routes = extract_routes(replay)
    print routes
    pdb.set_trace()
    with open('pos.out', 'w') as f:
        f.write(str(routes))
    #match['routes'] = routes
    #result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
