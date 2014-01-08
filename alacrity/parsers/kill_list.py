#!/usr/bin/python
# -*- coding: utf-8 -*-


from tarrasque import *
import sys
from ..config.api import get_match_details
from ..config.db import db
from inspect_props import dict_to_csv
from utils import HeroNameDict, unitIdx
from parser import Parser, run_single_parser
from preparsers import GameStartTime, PlayerHeroMap, PlayerTeamMap


import traceback
from collections import defaultdict

import pdb;

class KillParser(Parser):
    def __init__(self, replay):
        self.gst = GameStartTime().results
        self.player_hero_map = PlayerHeroMap().results
        self.player_team_map = PlayerTeamMap().results
        assert self.gst is not None
        assert self.player_hero_map is not None and len(self.player_hero_map) > 0
        assert self.player_team_map is not None and len(self.player_team_map) > 0
        self.deaths = []

    @property
    def tick_step(self):
        return 30

    def parse(self, replay):
        msgs = replay.user_messages
        kills = [msg[1] for msg in msgs if msg[0] == 66 and msg[1].type == 0]
        streak_kills = [msg[1] for msg in msgs if msg[0] == 66 and msg[1].type == 6]
        for death in kills:
            victimname = self.player_hero_map[death.playerid_1]
            if death.playerid_2 != -1:
                killername = self.player_hero_map[death.playerid_2]
                deny = True if self.player_team_map[death.playerid_1] == self.player_team_map[death.playerid_2] else False
            else:
                killername = victimname
                deny = True

            d = {'time': replay.info.game_time - self.gst,
                 'hero': victimname,
                 'killer': killername,
                 'bounty_gold': death.value,
                 'event': 'deny' if deny else 'kill'}
            self.deaths.append(d)
        for death in streak_kills:
            victimname = self.player_hero_map[death.playerid_4]
            if death.playerid_1 != -1:
                killername = self.player_hero_map[death.playerid_1]
                deny = True if self.player_team_map[death.playerid_4] == self.player_team_map[death.playerid_1] else False
            else:
                killername = victimname
                deny = True

            d = {'time': replay.info.game_time - self.gst,
                 'hero': victimname,
                 'killer': killername,
                 'killer_streak': death.playerid_2,
                 'victim_streak': death.playerid_5,
                 'bounty_gold': death.value,
                 'event': 'deny' if deny else 'kill'}
            self.deaths.append(d)

    @property
    def results(self):
        return {'kill_list':self.deaths}

def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    #match = db.find_one({'match_id': match_id}) or {}
    kill_list = run_single_parser(KillParser, replay)
    print kill_list
    #match.update(kill_list)
    #result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
