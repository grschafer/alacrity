#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from ..config.api import get_match_details
from ..config.db import db
from inspect_props import dict_to_csv
from utils import HeroNameDict, unitIdx
from parser import Parser
from preparsers import GameStartTime, PlayerHeroMap

import pdb
import traceback
from collections import defaultdict

class GraphParser(Parser):
    def __init__(self, replay):
        self.gst = GameStartTime().results
        self.player_hero_map = PlayerHeroMap().results
        assert self.gst is not None
        assert self.player_hero_map is not None and len(self.player_hero_map) > 0
        self.xp_dict = defaultdict(list)
        self.gold_dict = defaultdict(list)

    @property
    def tick_step(self):
        return 300

    def parse(self, replay):
        if replay.info.pausing_team:
            return
        self.xp_dict['time'].append(replay.info.game_time - self.gst)
        self.gold_dict['time'].append(replay.info.game_time - self.gst)
        for player in replay.players:
            name = self.player_hero_map[player.index]
            xp = player.hero.xp if player.hero else 0
            self.xp_dict[name].append(xp)
            gold = player.earned_gold
            self.gold_dict[name].append(gold)

    @property
    def results(self):
        return {'xp_graph':dict(self.xp_dict), 'gold_graph':dict(self.gold_dict)}


def extract_graphs(replay):
    replay.go_to_tick('postgame')
    parser = GraphParser(replay)
    for tick in replay.iter_ticks(start="pregame", end="postgame", step=parser.tick_step):
        parser.parse(replay)
    return parser.results


def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    graphs = extract_graphs(replay)
    #dict_to_csv('xp.csv', xp)
    #dict_to_csv('gold.csv', gold)
    #match['wards'] = wards
    match.update(graphs)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
