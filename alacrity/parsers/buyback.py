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

def buyback_cost(player, replay, gst):
    level = player.hero.level
    # convert time from seconds to minutes
    game_time = (replay.info.game_time - gst) / 60.
    raw = 100 + (level*level*1.5) + (game_time * 15)
    return int(raw)

class BuybackParser(Parser):
    def __init__(self, replay):
        assert replay.info.game_state == "postgame"
        self.gst = replay.info.game_start_time
        self.player_hero_map = {p.index:HeroNameDict[unitIdx(p.hero)]['name'] for p in replay.players}
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
            self.bb_cost = buyback_cost(pl, replay, self.gst)
            name = self.player_hero_map[msg.playerid_1]
            self.bbs.append({'time':(replay.info.game_time - self.gst), 'event':'buyback', 'cost':self.bb_cost, 'hero':name})

    @property
    def results(self):
        return {'buybacks':self.bbs}


# look in user_messages for chat_event type=7, buyback by player
def extract_buybacks(replay):
    replay.go_to_tick('postgame')
    parser = BuybackParser(replay)
    for tick in replay.iter_ticks(start="pregame", end="postgame", step=parser.tick_step):
        parser.parse(replay)
    return parser.results


def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    bbs = extract_buybacks(replay)
    print bbs
    match.update(bbs)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
