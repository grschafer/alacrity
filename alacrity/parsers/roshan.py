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
# look in combat log for death (4) of roshan (115)
# rosh_deaths = [x for x in msgs if isinstance(x, CombatLogMessage) and x.target_name == 'npc_dota_roshan' and x.type == 'death']
#
# or look in user_messages for chat_event type=9 and playerid_1 has team id (2 = radiant, 3 = dire)
# look in user_messages for chat_event type=8, picked up by playerid_1
# denied_aegis is chat_event type=51
# snatched_aegis is chat_event type=53
#
# OrderedDict([(u'type', 4), (u'sourcename', 11), (u'targetname', 115), (u'attackername', 11), (u'inflictorname', 0), (u'attackerillusion', False), (u'targetillusion', False), (u'value', 0), (u'health', 0), (u'timestamp', 2798.343994140625), (u'targetsourcename', 115)])

class RoshanParser(Parser):
    def __init__(self, replay):
        self.gst = GameStartTime().results
        self.player_hero_map = PlayerHeroMap().results
        self.player_team_map = PlayerTeamMap().results
        assert self.gst is not None
        assert self.player_hero_map is not None and len(self.player_hero_map) > 0
        assert self.player_team_map is not None and len(self.player_team_map) > 0
        self.roshs = []

    @property
    def tick_step(self):
        return 30

    def parse(self, replay):
        msgs = replay.user_messages
        rosh_deaths = [x[1] for x in msgs if x[0] == 66 and x[1].type == 9]
        aegis_take = [x[1] for x in msgs if x[0] == 66 and x[1].type == 8]
        aegis_snatch = [x[1] for x in msgs if x[0] == 66 and x[1].type == 53]
        aegis_deny = [x[1] for x in msgs if x[0] == 66 and x[1].type == 51]
        for msg in rosh_deaths:
            self.roshs.append({'time':replay.info.game_time - self.gst, 'event':'roshan_kill', 'team':self.player_team_map[msg.playerid_1]})
        for msg in aegis_take:
            self.roshs.append({'time':replay.info.game_time - self.gst, 'event':'aegis_pickup', 'hero':self.player_hero_map[msg.playerid_1]})
        for msg in aegis_snatch:
            self.roshs.append({'time':replay.info.game_time - self.gst, 'event':'aegis_stolen', 'hero':self.player_hero_map[msg.playerid_1]})
        for msg in aegis_deny:
            self.roshs.append({'time':replay.info.game_time - self.gst, 'event':'aegis_denied', 'hero':self.player_hero_map[msg.playerid_1]})

    @property
    def results(self):
        return {'roshans':self.roshs}

def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    roshs = run_single_parser(RoshanParser, replay)
    print roshs
    match.update(roshs)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
