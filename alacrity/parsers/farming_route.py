#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
import utils

import traceback
import pdb

# NEXT IDEAS
#  courier kills
#  mouse clicks and mouse travel distance
#  "possession"
#  bonus gold/xp from midas/devour/track?
#  item build times (for a finished item, how long did it take them to finish it?)

# CALL THIS "BEST 2-MINUTE CREEP GPM" instead of farming route?
# track both best 2min gpm and best 2min farming gpm (1st just earned_gold diff and 2nd counting only creep money)
def extract_routes(replay):
    top_farmer = []
    best2min = None
    cur_queue = []
    replay.go_to_tick('postgame')
    top_farmer = sorted(replay.players, key=lambda x: x.earned_gold / replay.info.game_end_time)[-3]
    top_farmer_name = utils.hero_dt_to_raw[top_farmer.hero.dt_key]

    # ADD IN PASSIVE GOLD INCREASE!
    pdb.set_trace()
    for tick in replay.iter_ticks(start="game", step=30):
        try:
            #evts = replay.game_events
            #farmer_kills = [x for x in evts if isinstance(x, CombatLogMessage) and x.type == 'death' and x.attacker_name == top_farmer_name and x.target_name.startswith('npc_dota_creep')]
            #for k in farmer_kills:
                # MATCH gold.target_entindex to k.target_name? otherwise, don't look through farmer kills
                # gets gold overhead messages given to topfarmer and gotten from a creep type
                golds = [x[1] for x in replay.user_messages if x[0] == 83 and x[1].message_type == 0 and top_farmer.ehandle == replay.world.by_index[x[1].target_player_entindex] and (u'DT_DOTA_BaseNPC_Creep', u'm_bIsWaitingToSpawn') in replay.world.find_index(x[1].target_entindex)]
                for g in golds:
                    print '{}: val {}    source {}    target {}    targetplayer {}'.format(tick, g.value, g.source_player_entindex, g.target_entindex, g.target_player_entindex)
                if golds:
                    3 + 4
                #print '{} {} {} killed {} {} for {}'.format(k.source_name, k.attacker_name, k.inflictorname, k.target_name, k.properties['targetsourcename'], [x.value for x in golds])
        except:
            traceback.print_exc()
            pdb.set_trace()


        #for pl in top_farmers:
        #    if pl.hero:
        #        x,y = pl.hero.position
        #        pos[pl.index].append((int(x),int(y)))

    # a queue of 2 minutes of {tick,x,y,earned_gold?} for each farmer
    # if combatlog contains 'farmer killed x' for x not a Creep_Lane/Creep_Neutral (convert raw names I guess), then flush queue
    #   this doesn't exclude tower kills, kill assists
    # MAYBE: if there is a gold overhead for farmer and not a corresponding last-hit count increase, then flush queue
    #   building kills go toward last hit count
    # each tick, if queue is full take max(existing_max, 2min_gpm) and if this is new max then deepcopy it
    # and push/pop current queue

    return pos

def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    routes = extract_routes(replay)
    print routes
    pdb.set_trace()
    with open('pos.out', 'w') as f:
        f.write(str(routes))
    #match['routes'] = routes
    #result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
