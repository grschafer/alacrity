#!/usr/bin/python
# -*- coding: utf-8 -*-

# boilerplate to allow running as script directly
# http://stackoverflow.com/a/6655098/751774
if __name__ == "__main__" and __package__ is None:
    import sys, os
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    while os.path.exists(os.path.join(parent_dir, '__init__.py')):
        parent_dir = os.path.dirname(parent_dir)
        sys.path.insert(1, parent_dir)
    import alacrity.parsers
    __package__ = "alacrity.parsers"
    del sys, os

from tarrasque import *
import sys
from ..config.api import get_match_details
from ..config.db import db
from inspect_props import dict_to_csv
from utils import HeroNameDict, unitIdx


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
gst = None # game_start_time
def extract_roshans(replay):
    roshs = []
    TEAMS = {2: 'radiant', 3: 'dire'}

    replay.go_to_tick('postgame')
    global gst
    gst = replay.info.game_start_time
    player_hero_map = {p.index:HeroNameDict[unitIdx(p.hero)]['name'] for p in replay.players}
    player_team_map = {p.index: p.hero.team for p in replay.players}

    for tick in replay.iter_ticks(start="pregame", end="postgame", step=30):
        #print 'tick: {}'.format(tick)
        msgs = replay.user_messages
        rosh_deaths = [x[1] for x in msgs if x[0] == 66 and x[1].type == 9]
        aegis_take = [x[1] for x in msgs if x[0] == 66 and x[1].type == 8]
        aegis_snatch = [x[1] for x in msgs if x[0] == 66 and x[1].type == 53]
        aegis_deny = [x[1] for x in msgs if x[0] == 66 and x[1].type == 51]
        for msg in rosh_deaths:
            roshs.append({'time':replay.info.game_time - gst, 'event':'roshan_kill', 'team':player_team_map[msg.playerid_1]})
        for msg in aegis_take:
            roshs.append({'time':replay.info.game_time - gst, 'event':'aegis_pickup', 'hero':player_hero_map[msg.playerid_1]})
        for msg in aegis_snatch:
            roshs.append({'time':replay.info.game_time - gst, 'event':'aegis_stolen', 'hero':player_hero_map[msg.playerid_1]})
        for msg in aegis_deny:
            roshs.append({'time':replay.info.game_time - gst, 'event':'aegis_denied', 'hero':player_hero_map[msg.playerid_1]})
    return {'roshans':roshs}


def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    roshs = extract_roshans(replay)
    print roshs
    match.update(roshs)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()