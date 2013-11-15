#!/usr/bin/python
# -*- coding: utf-8 -*-


from tarrasque import *
import sys
from ..config.api import get_match_details
from ..config.db import db
from inspect_props import dict_to_csv
from utils import HeroNameDict, unitIdx
from parser import Parser

import traceback
from collections import defaultdict


def get_gpm_xpm(player, replay, gst):
    game_started = replay.info.game_time > gst
    if not game_started:
        # then the game hasn't started yet
        return 0,0
    # add +1 to avoid div by zero if we land on the game_start_time tick
    gpm = int(60 * player.earned_gold / (replay.info.game_time - gst + 1))
    xpm = int(60 * player.hero.xp / (replay.info.game_time - gst + 1))
    return gpm,xpm

class ScoreboardParser(Parser):
    def __init__(self, replay):
        assert replay.info.game_state == "postgame"
        self.gst = replay.info.game_start_time
        self.player_hero_map = {p.index:HeroNameDict[unitIdx(p.hero)]['name'] for p in replay.players}

        self.scoreboards = []
        self.player_names = {self.player_hero_map[p.index]:p.name.decode('utf-8').replace('.',u'\uff0E') for p in replay.players}
        self.rad_gpm = sorted([p for p in replay.players if p.team == 'radiant'], key=lambda p: get_gpm_xpm(p, replay, self.gst)[0], reverse=True)
        self.dire_gpm = sorted([p for p in replay.players if p.team == 'dire'], key=lambda p: get_gpm_xpm(p, replay, self.gst)[0], reverse=True)
        self.player_teams = {'radiant': [self.player_hero_map[p.index] for p in self.rad_gpm],
                        'dire': [self.player_hero_map[p.index] for p in self.dire_gpm]}

    @property
    def tick_step(self):
        return 450

    def parse(self, replay):
        if replay.info.pausing_team:
            return
        scoreboard = {'time':replay.info.game_time - self.gst}
        for pl in replay.players:
            if not pl.hero:
                return
            name = HeroNameDict[unitIdx(pl.hero)]['name']
            gpm,xpm = get_gpm_xpm(pl, replay, self.gst)
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
        self.scoreboards.append(scoreboard)

    @property
    def results(self):
        return {'scoreboards':self.scoreboards, 'player_names': self.player_names, 'player_teams': self.player_teams}


def extract_scoreboards(replay):
    replay.go_to_tick('postgame')
    parser = ScoreboardParser(replay)
    for tick in replay.iter_ticks(start="pregame", end="postgame", step=parser.tick_step):
        parser.parse(replay)
    return parser.results



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
