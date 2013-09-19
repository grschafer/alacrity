#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import sys
from api import get_match_details
from db import db

@register_entity("DT_DotaSpecGraphPlayerData")
class Sgpd(DotaEntity):
    pass
@register_entity("DT_DOTASpectatorGraphManagerProxy")
class Sgmp(DotaEntity):
    pass


import traceback
from collections import defaultdict
def extract_graphs(replay):
    props = defaultdict(list)
    for tick in replay.iter_ticks(start="pregame", step=1800):
        sgpd = Sgpd.get_all(replay)
        sgmp = Sgmp.get_all(replay)
        props['tick'].append(tick)
        for p,v in sgmp[0].properties.iteritems():
            props[p].append(v)
    return props

def dict_to_csv(filename, d):
    with open(filename, 'wb') as f:
        #first = d.itervalues().next()
        #numcols = len(first) + 1
        #fmtstr = ('"{}",' * numcols)[:-1] + '\n'

        try:
            #f.write(fmtstr.format('tick', *d['tick']))
            for k,v in d.iteritems():
                f.write('"' + '","'.join([k] + [str(x) for x in v]) + "\"\n")
        except Exception:
            print traceback.format_exc()
            import pdb; pdb.set_trace()
            print 'test'

def main():
    dem_file = sys.argv[1] # pass replay as cmd-line argument!
    replay = StreamBinding.from_file(dem_file, start_tick="pregame")
    match_id = replay.info.match_id
    #match = get_match_details(match_id)
    graphs = extract_graphs(replay)
    dict_to_csv('graphs.csv', graphs)
    #match['wards'] = wards
    #result = db.update({'match_id': match_id}, match, upsert=True)

if __name__ == '__main__':
    main()
