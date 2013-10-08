#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from api import get_match_details
from db import db
from inspect_props import dict_to_csv
from utils import hero_id_to_raw


import traceback
from collections import defaultdict


import pdb

def extract_scoreboards(replay):
    scoreboards = []
    replay.go_to_tick('postgame')
    # add +1 to avoid div by zero if we land on the game_start_time tick
    gst = replay.info.game_start_time + 1
    # TODO: reverse key,value?
    players = {p.name.replace('.',u'\uff0E'):p.hero.name for p in replay.players}

    for tick in replay.iter_ticks(start="pregame", end="postgame", step=450):
        if replay.info.pausing_team:
            continue
        try:
            scoreboard = {'tick':tick}
            for pl in replay.players:
                if not pl.hero:
                    continue
                game_started = replay.info.game_time < gst
                scoreboard[pl.hero.name] = {
                    'l': pl.hero.level,
                    'k': pl.kills,
                    'd': pl.deaths,
                    'a': pl.assists,
                    'i0': pl.hero.inventory[0].name if len(pl.hero.inventory) > 0 else 0,
                    'i1': pl.hero.inventory[1].name if len(pl.hero.inventory) > 1 else 0,
                    'i2': pl.hero.inventory[2].name if len(pl.hero.inventory) > 2 else 0,
                    'i3': pl.hero.inventory[3].name if len(pl.hero.inventory) > 3 else 0,
                    'i4': pl.hero.inventory[4].name if len(pl.hero.inventory) > 4 else 0,
                    'i5': pl.hero.inventory[5].name if len(pl.hero.inventory) > 5 else 0,
                    'g':  pl.total_gold,
                    'lh': pl.last_hits,
                    'dn': pl.denies,
                    'gpm': int(60 * pl.earned_gold / (replay.info.game_time - gst) if game_started else 0),
                    'xpm': int(60 * pl.hero.xp / (replay.info.game_time - gst) if game_started else 0)
                }
            print "{}, {}".format(tick, len(scoreboard))
            scoreboards.append(scoreboard)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            pdb.set_trace()
            print 'leaving exception'

    return {'scoreboards':scoreboards, 'player_names': players}


def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file)
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    scoreboards = extract_scoreboards(replay)
    print scoreboards
    #pdb.set_trace()
    match.update(scoreboards)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
