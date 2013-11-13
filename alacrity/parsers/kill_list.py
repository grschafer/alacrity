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

@register_entity("DT_DOTA_Unit_Hero_Meepo")
class Meepo(Hero):
    pass

def get_heroes_in_radius(replay, target, radius):
    """Returns list of heroes within 1200 radius of target and on opposite team"""
    heroes = [p for p in replay.players if p.team in TEAMS.values() and p.team != target.team]
    def within_radius(a,b, radius):
        return ((a.position[0] - b.position[0])**2 + (a.position[1] - b.position[1])**2) <= radius ** 2
    # meepo is torture
    if target.hero.name == 'Meepo':
        meepos = Meepo.get_all(replay)
        heroes = [p for p in heroes if any([within_radius(p.hero, m, radius) for m in meepos])]
    else:
        heroes = [p for p in heroes if within_radius(p.hero, target.hero, radius)]
    return heroes

class Streak(list):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Streak, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    _STREAK = [0,0,0,75,150,225,300,375,450,525,600]
    def __getitem__(self, x):
        return 600 if x > 10 else Streak._STREAK[x]
STREAK_GOLD = Streak()
# http://dota2.gamepedia.com/Gold#Kills
# GOLD_AREA(# heroes within 1200, level of enemy killed)
GOLD_AREA = lambda num, level: _GOLD_AREA[num](level) * num
_GOLD_AREA = {0: lambda level: 0,
              1: lambda level: 125 + level * 12,
              2: lambda level: (40 + level * 10),
              3: lambda level: (10 + level * 6),
              4: lambda level: (level * 6),
              5: lambda level: (level * 6)}
# http://dota2.gamepedia.com/Experience#Experience_Formula
# XP_AREA(# heroes within 1200, level of enemy killed)
XP_AREA = lambda num, level: int(_XP_AREA[num](level) * (num if num > 0 else 1))
_XP_AREA = {0: lambda level: _XP_AREA[1](level),
            1: lambda level: 220 if level == 0 else (level * 20 + _XP_AREA[1](level - 1) if level < 5 else 120 * level - 80),
            2: lambda level: 140 if level == 0 else (level * 10 + 5 + _XP_AREA[2](level - 1) if level < 5 else 65 * level - 10),
            3: lambda level: 64 + 1./6 if level == 0 else (level * (121./18) + _XP_AREA[3](level - 1) if level < 5 else (121 * level - 110)/3.),
            4: lambda level: 45 if level == 0 else (level * 5 + _XP_AREA[4](level - 1) if level < 5 else 30 * level - 30),
            5: lambda level: 35 if level == 0 else (level * 4 + _XP_AREA[5](level - 1) if level < 5 else 24 * level - 25)}

# WHAT ABOUT BH TRACK KILLS?
def gold_xp_from_kill(replay, victim, firstblood=False, deny=False):
    """Total gold and xp given away from killing the victim"""
    near_heroes = get_heroes_in_radius(replay, victim, 1300)
    num_heroes = len(near_heroes)
    #gold = STREAK_GOLD[victim.streak] + 200 + victim.hero.level * 9 + 200 if firstblood else 0
    xp = XP_AREA(num_heroes, victim.hero.level) if not deny else 0

    # check killer
    gold = get_gold_overheads(replay) if not deny else 0
    #if killer in near_heroes:
    #    num_heroes -= 1
    #gold += GOLD_AREA(num_heroes, victim.hero.level)
    return gold, xp

# MEMOIZE THIS
def index_to_id(replay, idx):
    return replay.world.find_index(idx)[('DT_DOTAPlayer', 'm_iPlayerID')]

# HERO NAME: hero.property[(u'DT_DOTA_BaseNPC', u'm_iUnitNameIndex')] for indexing into GetHeroes API call

def get_gold_overheads(replay):
    msgs = replay.user_messages
    golds = [m[1].value for m in msgs if m[0] == 83 and m[1].message_type == 0]
    print '  gold overheads:{}'.format(golds)
    return sum(golds)


def get_killers(replay, victim):
    """Only returns multiple people if the kill was split (i.e. a tower/creep got lasthit)"""
    msgs = replay.user_messages
    #kill_msgs = [m for m in msgs if m[0] == 66 and m[1].type == 0] # hero_kill or streak_kill
    #kill_msg = [m for m in kill_msgs if m[1].playerid_1 == victim.index]
    kill_msgs = [m for m in msgs if m[0] == 66 and (m[1].type == 0 or m[1].type == 6)] # hero_kill or streak_kill
    kill_msg = [m for m in kill_msgs if (m[1].type == 0 and m[1].playerid_1 == victim.index) or (m[1].type == 6 and m[1].playerid_4 == victim.index)]

    # if there are multiple messages left, they're for the same kill (1 message each for kill and killstreak)
    kill_msg = kill_msg[0][1]
    if kill_msg.type == 0:
        killers = set([getattr(kill_msg, 'playerid_{}'.format(x)) for x in range(2,6)])
        killers = [p for p in replay.players if p.index in killers]
    elif kill_msg.type == 6:
        killers = [p for p in replay.players if p.index == kill_msg.playerid_1]
    else:
        print 'kill_msg type is not 0 (kill) or 6 (killstreak)!'
        pdb.set_trace()
    print '  killers:{}'.format([(x.name, x.hero.name) for x in killers])
    return killers


import pdb;

TEAMS = {2: 'radiant', 3: 'dire'}
gst = None # game_start_time
def extract_kill_list(replay):
    deaths = []
    # ALSO NEED DICTS OF RAW NAMES (npc_dota_hero_nevermore) AND ENT_INDEX (2)?
    # raw names needs to include towers, creeps (lane/neutral), and fountain
    replay.go_to_tick('postgame')
    global gst
    gst = replay.info.game_start_time
    player_hero_map = {p.index:HeroNameDict[unitIdx(p.hero)]['name'] for p in replay.players}

    for tick in replay.iter_ticks(start="pregame", end="postgame", step=30):
        try:
            #print 'tick: {}, gametime: {}'.format(tick, replay.info.game_time - gst)
            msgs = replay.user_messages
            kills = [msg[1] for msg in msgs if msg[0] == 66 and msg[1].type == 0]
            streak_kills = [msg[1] for msg in msgs if msg[0] == 66 and msg[1].type == 6]
            for death in kills:
                victim = [x for x in replay.players if x.index == death.playerid_1][0]
                killer = [x for x in replay.players if x.index == death.playerid_2][0]
                deny = True if killer.team == victim.team else False
                d = {'time': replay.info.game_time - gst,
                     'hero':HeroNameDict[victim.hero.dt_key]['name'],
                     'killer':HeroNameDict[killer.hero.dt_key]['name'],
                     'bounty_gold': death.value,
                     'event': 'deny' if deny else 'kill'}
                deaths.append(d)
                print d
            for death in streak_kills:
                victim = [x for x in replay.players if x.index == death.playerid_4][0]
                killer = [x for x in replay.players if x.index == death.playerid_1][0]
                deny = True if killer.team == victim.team else False
                d = {'time': replay.info.game_time - gst,
                     'hero':HeroNameDict[victim.hero.dt_key]['name'],
                     'killer':HeroNameDict[killer.hero.dt_key]['name'],
                     'killer_streak': death.playerid_2,
                     'victim_streak': death.playerid_5,
                     'bounty_gold': death.value,
                     'event': 'deny' if deny else 'kill'}
                deaths.append(d)
                print d
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print '*** print_tb'
            traceback.print_tb(exc_traceback)
            print '*** print_exception'
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            print '*** print_exc'
            traceback.print_exc()
            pdb.set_trace()
            print 'done'

    #pdb.set_trace()
    return {'kill_list':deaths}


def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    match = db.find_one({'match_id': match_id}) or {}
    kill_list = extract_kill_list(replay)
    print kill_list
    match.update(kill_list)
    result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
