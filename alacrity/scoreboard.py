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


import pdb

def get_gpm_xpm(player, replay):
    if replay.info.game_start_time is None:
        # then the game hasn't started yet
        return 0,0
    gst = replay.info.game_start_time + 1
    game_started = replay.info.game_time > gst
    gpm = int(60 * player.earned_gold / (replay.info.game_time - gst) if game_started else 0),
    xpm = int(60 * player.hero.xp / (replay.info.game_time - gst) if game_started else 0)
    return gpm,xpm

def extract_scoreboards(replay):
    scoreboards = []
    replay.go_to_tick('postgame')
    player_hero_map = {p.index:HeroNameDict[unitIdx(p.hero)]['name'] for p in replay.players}
    # add +1 to avoid div by zero if we land on the game_start_time tick
    # TODO: reverse key,value?
    TEAMS = {2: 'radiant', 3:'dire'}
    player_names = {player_hero_map[p.index]:p.name.replace('.',u'\uff0E') for p in replay.players}
    rad_gpm = sorted([p for p in replay.players if p.team == 'radiant'], key=lambda p: get_gpm_xpm(p, replay)[0], reverse=True)
    dire_gpm = sorted([p for p in replay.players if p.team == 'dire'], key=lambda p: get_gpm_xpm(p, replay)[0], reverse=True)
    player_teams = {'radiant': [player_hero_map[p.index] for p in rad_gpm],
                    'dire': [player_hero_map[p.index] for p in dire_gpm]}

    for tick in replay.iter_ticks(start="pregame", end="postgame", step=450):
        if replay.info.pausing_team:
            continue
        try:
            scoreboard = {'time':replay.info.game_time}
            for pl in replay.players:
                if not pl.hero:
                    continue
                name = HeroNameDict[unitIdx(pl.hero)]['name']
                gpm,xpm = get_gpm_xpm(pl, replay)
                scoreboard[name] = {
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
                    'gpm': gpm,
                    'xpm': xpm
                }
            #print "{}, {}".format(tick, len(scoreboard))
            scoreboards.append(scoreboard)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            pdb.set_trace()
            print 'leaving exception'

    return {'scoreboards':scoreboards, 'player_names': player_names, 'player_teams': player_teams}


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
