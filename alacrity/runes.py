#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from api import get_match_details
from db import db
from inspect_props import dict_to_csv
from utils import HeroNameDict, unitIdx, baseent_coords


import traceback
from collections import defaultdict
# look in user_messages for chat_event type=22 (pickup/use bottled) and type=23 (bottle)
# look for Rune entity

RUNES = {0: 'doubledamage', 1: 'haste', 2: 'illusion', 3: 'invis', 4: 'regen' }

@register_entity("DT_DOTA_Item_Rune")
class Rune(DotaEntity):
    pass

gst = None # game_start_time
def extract_runes(replay):
    runes = set()
    rune_actions = []
    TEAMS = {2: 'radiant', 3: 'dire'}

    replay.go_to_tick('postgame')
    global gst
    gst = replay.info.game_start_time
    player_hero_map = {p.index:HeroNameDict[unitIdx(p.hero)]['name'] for p in replay.players}

    for tick in replay.iter_ticks(start="pregame", end="postgame", step=30):
        #print 'tick: {}'.format(tick)
        runes_spawned = Rune.get_all(replay)
        for r in runes_spawned:
            if r.ehandle not in runes:
                runes.add(r.ehandle)
                pos = baseent_coords(r)
                rune_actions.append({'time':replay.info.game_time - gst, 'event':'rune_spawn', 'x':pos[0], 'y':pos[1], 'rune_type':RUNES[r.properties[('DT_DOTA_Item_Rune', 'm_iRuneType')]]})

        msgs = replay.user_messages
        pickups = [x[1] for x in msgs if x[0] == 66 and x[1].type == 22]
        bottles = [x[1] for x in msgs if x[0] == 66 and x[1].type == 23]
        for msg in pickups:
            rune_actions.append({'time':replay.info.game_time - gst, 'event':'rune_pickup', 'rune_type': RUNES[msg.value], 'hero':player_hero_map[msg.playerid_1]})
        for msg in bottles:
            rune_actions.append({'time':replay.info.game_time - gst, 'event':'rune_bottle', 'rune_type': RUNES[msg.value], 'hero':player_hero_map[msg.playerid_1]})
    return {'runes':rune_actions}


def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    runes = extract_runes(replay)
    match.update(runes)
    print runes
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
