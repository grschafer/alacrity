#!/usr/bin/python
# -*- coding: utf-8 -*-

import pymongo
from tarrasque import *
from urllib2 import urlopen
import json
import os
from ConfigParser import ConfigParser
import argparse

def get_db(config):
    db_config = (config.get('db', 'host'), config.getint('db', 'port'))
    db_name = config.get('db', 'db_name')
    collection_name = config.get('db', 'collection_name')

    client = pymongo.mongo_client.MongoClient(*db_config)
    db = client[db_name][collection_name]
    db.ensure_index('match_id', pymongo.ASCENDING)
    return db


@register_entity("DT_DOTA_NPC_Observer_Ward")
class Ward(BaseNPC):
    pass
    #def __init__(self, *args, **kwargs):
    #    super(Ward, self).__init__(*args, **kwargs)
    #    if self.ehandle not in wards:
    #        wards[self.ehandle] = (self.position, self.team, self.tick)
    #        print '{}: {} {} {}'.format(self.ehandle, self.position, self.team, self.tick)

def extract_wards(replay):
    wards = {}
    for tick in replay.iter_ticks(start="pregame", step=300):
        wardlist = Ward.get_all(replay)
        for w in wardlist:
            if w.ehandle not in wards:
                wards[w.ehandle] = {
                        'x': w.position[0],
                        'y': w.position[1],
                        'team': w.team,
                        'tick': w.tick
                    }
    return wards.values()

def fetch_match_details(api_key, match_id):
    url = 'http://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v1?key={}&match_id={}'.format(api_key, match_id)
    resp = urlopen(url)
    # TODO: error checking
    body = resp.read()
    match = json.loads(body)['result']
    return match

def endswith(array, ending):
    for x in array:
        if x.endswith(ending):
            yield x

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('target_dir',
                        help='directory to process .dem files from')
    parser.add_argument('-f', action='store_true',
                        help='force re-processing for matches already found in db')
    parser.add_argument('-r', action='store_true',
                        help='parse .dem files in sub-directories')
    args = parser.parse_args()
    config = ConfigParser()
    config.read('config.cfg')
    db = get_db(config)
    api_key = config.get('api', 'key')

    try:
        for root, dirs, files in os.walk(args.target_dir):
            for fname in endswith(files, '.dem'):
                path = os.path.join(root, fname)
                print 'processing match from {}'.format(path)

                # KeyError for recv_table (update entity that doesn't exist?)
                try:
                    replay = StreamBinding.from_file(path)
                except KeyError as e:
                    print e
                    replay = StreamBinding.from_file(path, start_tick=0)

                match_id = replay.info.match_id
                print '  match id {}'.format(match_id)

                if args.f or db.find_one({'match_id': match_id}) is None:
                    wards = extract_wards(replay)
                    print '  contains {} wards'.format(len(wards))

                    match = fetch_match_details(api_key, match_id)
                    print '  match details: {} vs {}, radiant_win: {}'.format(match.get('radiant_name', ''), match.get('dire_name', ''), match['radiant_win'])

                    match['wards'] = wards
                    result = db.update({'match_id': match_id}, match, upsert=True)
                    print '  result: {}'.format(result)
                else:
                    print '  match already exists in database, skipping...'

            # don't walk sub-directories unless -r flag supplied
            if not args.r:
                del dirs[:]
    except Exception as e:
        import sys
        print sys.exc_info()
        import traceback
        print traceback.format_exc()
        import pdb; pdb.set_trace()

if __name__ == '__main__':
    main()
