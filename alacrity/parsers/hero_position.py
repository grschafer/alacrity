#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from ..config.api import get_match_details
from ..config.db import db
from collections import defaultdict
from utils import HeroNameDict, unitIdx
from parser import Parser, run_single_parser
from preparsers import GameStartTime, PlayerHeroMap

import traceback
import pdb

class PositionParser(Parser):
    def __init__(self, replay):
        self.gst = GameStartTime().results
        self.player_hero_map = PlayerHeroMap().results
        assert self.gst is not None
        assert self.player_hero_map is not None and len(self.player_hero_map) > 0
        self.pos = defaultdict(list)

    @property
    def tick_step(self):
        return 30

    def parse(self, replay):
        if replay.info.pausing_team:
            return
        for idx,name in self.player_hero_map.iteritems():
            pl = [p for p in replay.players if p.index == idx]
            if len(pl) == 0 or pl[0].hero is None:
                x = y = -8000
                hp_pct = 1.0
                self.pos[name].append((x, y, hp_pct))
            else:
                pl = pl[0]
                x,y = pl.hero.position
                hp_pct = int(float(pl.hero.health) / pl.hero.max_health * 100)
                self.pos[name].append((int(x),int(y),hp_pct))
        self.pos['time'].append(replay.info.game_time - self.gst)

    @property
    def results(self):
        return {'positions':dict(self.pos)}


def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    positions = run_single_parser(PositionParser, replay)
    print positions
    #with open('pos.out', 'w') as f:
    #    f.write(str(positions))
    match.update(positions)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
