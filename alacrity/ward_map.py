#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from api import get_match_details
from db import db

@register_entity("DT_DOTA_NPC_Observer_Ward")
class Ward(BaseNPC):
    pass
    #def __init__(self, *args, **kwargs):
    #    super(Ward, self).__init__(*args, **kwargs)
    #    if self.ehandle not in wards:
    #        wards[self.ehandle] = (self.position, self.team, self.tick)
    #        print '{}: {} {} {}'.format(self.ehandle, self.position, self.team, self.tick)

def extract_wards(replay):
    """
    Returns [{x:1234, y:-1234, team:radiant|dire, tick:2468}, ...]
    """
    wards = {}
    for tick in replay.iter_ticks(start="pregame", end="postgame", step=300):
        wardlist = Ward.get_all(replay)
        for w in wardlist:
            if w.ehandle not in wards:
                wards[w.ehandle] = {
                        'x': w.position[0],
                        'y': w.position[1],
                        'team': w.team,
                        'time': replay.info.game_time
                    }
    return {'wards':wards.values()}

def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    wards = extract_wards(replay)
    match.update(wards)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
