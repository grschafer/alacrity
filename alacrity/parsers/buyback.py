#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from ..config.api import get_match_details
from ..config.db import db
from inspect_props import dict_to_csv
from utils import HeroNameDict, unitIdx
from parser import Parser, run_single_parser
from preparsers import GameStartTime, PlayerHeroMap

import traceback
from collections import defaultdict

def buyback_cost(player, replay, gst):
    level = player.hero.level
    # convert time from seconds to minutes
    game_time = (replay.info.game_time - gst) / 60.
    raw = 100 + (level*level*1.5) + (game_time * 15)
    return int(raw)

class BuybackParser(Parser):
    def __init__(self, replay):
        self.gst = GameStartTime().results
        self.player_hero_map = PlayerHeroMap().results
        assert self.gst is not None
        assert self.player_hero_map is not None and len(self.player_hero_map) > 0
        self.bbs = []
        self.bb_cost = None

    @property
    def tick_step(self):
        return 30

    def parse(self, replay):
        if replay.info.pausing_team:
            return
        msgs = replay.user_messages
        buybacks = [x[1] for x in msgs if x[0] == 66 and x[1].type == 7]
        for msg in buybacks:
            pl = [p for p in replay.players if p.index == msg.playerid_1][0]
            bb_cost = buyback_cost(pl, replay, self.gst)
            name = self.player_hero_map[msg.playerid_1]
            self.bbs.append({'time':(replay.info.game_time - self.gst), 'event':'buyback', 'cost':bb_cost, 'hero':name})

    @property
    def results(self):
        return {'buybacks':self.bbs}


def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    bbs = run_single_parser(BuybackParser, replay)
    print bbs
    match.update(bbs)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
