#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from ..config.api import get_match_details
from ..config.db import db
from collections import defaultdict
from utils import HeroNameDict, unitIdx
from parser import Parser

import traceback
import pdb

class PositionParser(Parser):
    def __init__(self, replay):
        assert replay.info.game_state == "postgame"
        self.gst = replay.info.game_start_time
        self.player_hero_map = {p.index:HeroNameDict[unitIdx(p.hero)]['name'] for p in replay.players}
        self.pos = defaultdict(list)

    @property
    def tick_step(self):
        return 30

    def parse(self, replay):
        if replay.info.pausing_team:
            return
        for pl in replay.players:
            if pl and pl.hero:
                name = self.player_hero_map[pl.index]
                x,y = pl.hero.position if pl.hero else (0,0)
                hp_pct = int(float(pl.hero.health) / pl.hero.max_health * 100)
                self.pos[name].append((int(x),int(y),hp_pct))
        self.pos['time'].append(replay.info.game_time - self.gst)

    @property
    def results(self):
        return {'positions':dict(self.pos)}


def extract_positions(replay):
    replay.go_to_tick('postgame')
    parser = PositionParser(replay)
    for tick in replay.iter_ticks(start="pregame", end="postgame", step=parser.tick_step):
        parser.parse(replay)
    return parser.results


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
