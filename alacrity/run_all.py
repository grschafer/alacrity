#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import os
import argparse
import pdb
import traceback

# helpers
from db import db
from api import get_match_details

# analysis functions
from ward_map import extract_wards
from buyback import extract_buybacks
#from escapes import extract_escapes
from gold_xp_graphs import extract_graphs
from hero_position import extract_positions
from kill_list import extract_kill_list
from roshan import extract_roshans
from runes import extract_runes
from scoreboard import extract_scoreboards


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

    for root, dirs, files in os.walk(args.target_dir):
        for fname in endswith(files, '.dem'):
            path = os.path.join(root, fname)
            print 'processing match from {}'.format(path)

            replay = StreamBinding.from_file(path, start_tick=0)
            match_id = replay.info.match_id
            print '  match id {}'.format(match_id)

            if args.f or db.find_one({'match_id': match_id}) is None:
                match = get_match_details(match_id)
                #print '  match details: {} vs {}, radiant_win: {}'.format(match.get('radiant_name', ''), match.get('dire_name', ''), match['radiant_win'])
                #match = {'match_id': match_id}

                extract_funcs = [
                        extract_wards,
                        extract_buybacks,
                        #extract_escapes,
                        extract_graphs,
                        extract_positions,
                        #extract_kill_list,
                        extract_roshans,
                        extract_runes,
                        extract_scoreboards,
                        ]
                collected = []
                for extract in extract_funcs:
                    try:
                        collected.append(extract(replay))
                    except Exception as e:
                        print 'extraction failed for {}'.format(extract)
                        traceback.print_exc()
                        pdb.set_trace()
                        print 'done'

                for x in collected:
                    match.update(x)
                result = db.update({'match_id': match_id}, match, upsert=True)
                print '  result: {}'.format(result)
            else:
                print '  match already exists in database, skipping...'

        # don't walk sub-directories unless -r flag supplied
        if not args.r:
            del dirs[:]

if __name__ == '__main__':
    main()
