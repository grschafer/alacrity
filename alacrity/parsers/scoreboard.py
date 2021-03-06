#!/usr/bin/python
# -*- coding: utf-8 -*-


from tarrasque import *
import sys
import string
from ..config.api import get_match_details
from ..config.db import db
from inspect_props import dict_to_csv
from utils import HeroNameDict, unitIdx
from parser import Parser, run_single_parser
from preparsers import GameStartTime, PlayerHeroMap, HeroNameMap

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
        self.gst = GameStartTime().results
        self.player_hero_map = PlayerHeroMap().results
        assert self.gst is not None
        assert self.player_hero_map is not None and len(self.player_hero_map) > 0

        self.scoreboards = []

    @property
    def tick_step(self):
        return 450

    def parse(self, replay):
        if replay.info.pausing_team:
            return
        scoreboard = {'time':replay.info.game_time - self.gst}
        try:
            team_gold = {
                    'radiant': replay.world.find_by_dt('DT_DOTA_DataRadiant')[1],
                    'dire': replay.world.find_by_dt('DT_DOTA_DataDire')[1]
                    }
        except KeyError:
            team_gold = False

        for idx,name in self.player_hero_map.iteritems():
            player = [p for p in replay.players if p.index == idx]
            if len(player) == 0:
                if len(self.scoreboards) > 0:
                    scoreboard[name] = self.scoreboards[-1][name]
                else:
                    scoreboard[name] = {'l': 0, 'k': 0, 'd': 0, 'a': 0, 'i0': 0, 'i1': 0, 'i2': 0, 'i3': 0, 'i4': 0, 'i5': 0, 'g': 0, 'lh': 0, 'dn': 0, 'gpm': 0, 'xpm': 0}
                continue

            pl = player[0]
            if pl.hero is None:
                continue

            gpm,xpm = get_gpm_xpm(pl, replay, self.gst)
            # gold values stored differently in replays now
            if team_gold:
                gold = team_gold[pl.team][(u'DT_DOTA_DataNonSpectator', 'm_iReliableGold.000{}'.format(idx))] + team_gold[pl.team][(u'DT_DOTA_DataNonSpectator', 'm_iUnreliableGold.000{}'.format(idx))]
            else:
                gold = pl.total_gold

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
                #'g':  pl.total_gold,
                'g':  gold,
                'lh': pl.last_hits,
                'dn': pl.denies,
                'gpm': gpm,
                'xpm': xpm
            }
        self.scoreboards.append(scoreboard)

    @property
    def results(self):
        return {'scoreboards':self.scoreboards}

    def end_game(self, replay):
        self.parse(replay)

def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file)
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    scoreboards = run_single_parser(ScoreboardParser, replay)
    print scoreboards
    #pdb.set_trace()
    match.update(scoreboards)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
