#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from ..config.api import get_match_details
from ..config.db import db
from parser import Parser, run_single_parser
from preparsers import GameStartTime

import pdb
import traceback

WARD_NAMEIDX = 207
SENTRY_NAMEIDX = 208 # only way to differentiate wards pre-6.79

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

class WardParser(Parser):
    """
    Returns [{x:1234, y:-1234, event:add|rm, team:radiant|dire, type:obs|sentry, time:468.12, id:123445}, ...]
    """

    def __init__(self, replay):
        self.gst = GameStartTime().results
        assert self.gst is not None
        self.ward_events = []
        self.cur_wards = set()

    @property
    def tick_step(self):
        return 30

    def parse(self, replay):
        wardlist = Ward.get_all(replay) + Sentry.get_all(replay)
        for w in wardlist:
            if w.ehandle not in self.cur_wards:
                ward_type = "obs"
                if w.properties[('DT_DOTA_BaseNPC', 'm_iUnitNameIndex')] == SENTRY_NAMEIDX:
                    ward_type = "sentry"
                self.cur_wards.add(w.ehandle)
                self.ward_events.append({
                    'x': w.position[0],
                    'y': w.position[1],
                    'id': w.ehandle,
                    'team': w.team,
                    'type': ward_type,
                    'time': replay.info.game_time - self.gst,
                    'event': 'add',
                    })
        to_remove = []
        for ehandle in self.cur_wards:
            try:
                replay.world.find(ehandle)
            except KeyError:
                self.ward_events.append({
                    'id': ehandle,
                    'time': replay.info.game_time - self.gst,
                    'event': 'rm',
                    })
                to_remove.append(ehandle)

        for ehandle in to_remove:
            self.cur_wards.remove(ehandle)

    @property
    def results(self):
        return {'wards': self.ward_events}


def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    wards = run_single_parser(WardParser, replay)
    print wards
    match.update(wards)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
