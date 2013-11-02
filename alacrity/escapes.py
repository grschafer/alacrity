#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from api import get_match_details
from db import db
from inspect_props import dict_to_csv
from utils import HeroNameDict, unitIdx


import traceback
from collections import defaultdict
import pdb;

TEAMS = {2: 'radiant', 3: 'dire'}
gst = None # game_start_time
def extract_escapes(replay):
    near_deaths = []
    watchlist = []
    replay.go_to_tick('postgame')
    global gst
    gst = replay.info.game_start_time
    player_hero_map = {p.index:HeroNameDict[unitIdx(p.hero)]['name'] for p in replay.players}
    players = {p.index:p for p in replay.players}

    for tick in replay.iter_ticks(start="pregame", end="postgame", step=30):
        try:
            # add hero to watchlist if they're alive, under 5%, and not already on the watchlist
            for pl in replay.players:
                if pl.hero and pl.hero.health < 0.08 * pl.hero.max_health and pl.hero.life_state == "alive" and pl.index not in [x['id'] for x in watchlist]:
                    watchlist.append({'hero': player_hero_map(pl.index), 'id': pl.index, 'time': (replay.info.game_time - gst), 'escape': []})
                    print '{}: watching {} at {} hp, current set: {}'.format(tick, pl.hero.name, pl.hero.health, [x['hero'] for x in watchlist])

            # remove watched "escapes" where the hero died within 30 seconds of being under 5% hp
            watchlist = [w for w in watchlist if players[w['id']].hero.life_state == 'alive']

            # move watched escapes to near_deaths list if they've been watched for 30 seconds
            escapes = [w for w in watchlist if w['time'] + 30 < (replay.info.game_time - gst)]
            for e in escapes:
                print 'escape: {} at {} with {} escape points'.format(e['hero'], e['time'], len(e['escape']))
            near_deaths.extend(escapes)
            watchlist = [w for w in watchlist if w['time'] + 30 >= (replay.info.game_time - gst)]

            # add hero's current x, y, health, tick to escape
            for w in watchlist:
                hero = players[w['id']].hero
                w['escape'].append({'x': hero.position[0], 'y': hero.position[1], 'hp': hero.health, 'time': (replay.info.game_time - gst)})
        except:
            traceback.print_exc()
            pdb.set_trace()

    return {'escapes':near_deaths}


def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="postgame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    escapes = extract_escapes(replay)
    print escapes
    match.update(escapes)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
