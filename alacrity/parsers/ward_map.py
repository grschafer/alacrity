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

import pdb
import traceback

@register_entity("DT_DOTA_NPC_Observer_Ward")
class Ward(BaseNPC):
    pass
    #def __init__(self, *args, **kwargs):
    #    super(Ward, self).__init__(*args, **kwargs)
    #    if self.ehandle not in wards:
    #        wards[self.ehandle] = (self.position, self.team, self.tick)
    #        print '{}: {} {} {}'.format(self.ehandle, self.position, self.team, self.tick)

# this sentry DT-type was introduced in 6.79
@register_entity("DT_DOTA_NPC_Observer_Ward_TrueSight")
class Sentry(BaseNPC):
    pass

ward_nameidx = 207
sentry_nameidx = 208 # only way to differentiate wards pre-6.79
gst = None # game_start_time
def extract_wards(replay):
    """
    Returns [{x:1234, y:-1234, event:add|rm, team:radiant|dire, type:obs|sentry, time:468.12, id:123445}, ...]
    """
    ward_events = []
    cur_wards = set()

    replay.go_to_tick("game")
    global gst
    gst = replay.info.game_start_time

    for tick in replay.iter_ticks(start="pregame", end="postgame", step=30):
        wardlist = Ward.get_all(replay) + Sentry.get_all(replay)
        for w in wardlist:
            if w.ehandle not in cur_wards:
                ward_type = "obs"
                if w.properties[('DT_DOTA_BaseNPC', 'm_iUnitNameIndex')] == sentry_nameidx:
                    ward_type = "sentry"
                cur_wards.add(w.ehandle)
                ward_events.append({
                    'x': w.position[0],
                    'y': w.position[1],
                    'id': w.ehandle,
                    'team': w.team,
                    'type': ward_type,
                    'time': replay.info.game_time - gst,
                    'event': 'add',
                    })
        to_remove = []
        for ehandle in cur_wards:
            try:
                replay.world.find(ehandle)
            except KeyError:
                ward_events.append({
                    'id': ehandle,
                    'time': replay.info.game_time - gst,
                    'event': 'rm',
                    })
                to_remove.append(ehandle)

        for ehandle in to_remove:
            cur_wards.remove(ehandle)


    return {'wards': ward_events}

def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    wards = extract_wards(replay)
    print wards
    match.update(wards)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
