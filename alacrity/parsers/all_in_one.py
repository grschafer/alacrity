#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import os
import argparse
import pdb
import traceback

# helpers
from alacrity.config.db import db, errorgame_db
import alacrity.config.api as api
from parser import Parser
from preparsers import run_all_preparsers, MatchMetadata, DuplicateHeroException

from ward_map import WardParser
from buyback import BuybackParser
from gold_xp_graphs import GraphParser
from hero_position import PositionParser
from building_hp import BuildingHpParser
from kill_list import KillParser
from roshan import RoshanParser
from runes import RuneParser
from scoreboard import ScoreboardParser

# __subclasses__() will contain all the subclasses of the
# base Parser class that are imported in this scope
parser_classes = Parser.__subclasses__()

def parse_replay(replay):
    # preparsers populate mappings (between heroes, players, teams, etc.)
    # for use by the parsers
    # preparsers are singletons so parsers use this data by importing
    # the preparser they need and getting its results (e.g. GameStartTime().results)
    run_all_preparsers(replay)

    replay.go_to_tick("pregame") # some parser init depends on pregame state
    parsers = []
    for parser in parser_classes:
        parsers.append(parser(replay))

    # iter ticks and on every tick, pass replay reference to
    # each parser that wants it (depending on parser's tick_step)
    min_tick_step = min(p.tick_step for p in parsers) # 30
    interval = {p:0 for p in parsers}
    for tick in replay.iter_ticks(start="pregame", end="postgame", step=min_tick_step):
        for parser in parsers:
            interval[parser] -= min_tick_step
            if interval[parser] <= 0:
                parser.parse(replay)
                interval[parser] = parser.tick_step
    for parser in parsers:
        parser.end_game(replay)

    result = {}
    for parser in parsers:
        result.update(parser.results)
    return result


def endswith(array, ending):
    for x in array:
        if x.endswith(ending):
            yield x

def process_replays(directory, recurse=False, force=False):
    match_ids = []
    for root, dirs, files in os.walk(directory):
        for fname in endswith(files, '.dem'):
            path = os.path.join(root, fname)
            print 'processing match from {}'.format(path)

            replay = StreamBinding.from_file(path)

            # provides match_id, leagueid, duration, radiant_win, etc.
            metadata = MatchMetadata(replay).results
            match_id = metadata['match_id']
            match_ids.append(match_id)
            print '  match id {}'.format(match_id)

            if force or db.find_one({'match_id': match_id}) is None:
                match = db.find_one({'match_id': match_id}) or metadata

                # this data extracted from replay by MatchMetadata now
                #api_match = api.get_match_details(match_id)
                #assert 'error' not in api_match['result']
                #match.update(api_match['result'])
                print '  match details: {} vs {}, radiant_win: {}'.format(match.get('radiant_name', ''), match.get('dire_name', ''), match['radiant_win'])

                try:
                    parsed = parse_replay(replay)
                    match.update(parsed)
                    result = db.update({'match_id': match_id}, match, upsert=True)
                    print '  result: {}'.format(result)
                except DuplicateHeroException as e:
                    # don't want to interrupt the celery workflow
                    # e.g. - replay should still be deleted
                    traceback.print_exc()
                    errorgame_db.insert({'match_id': match_id})

            else:
                print '  match already exists in database, skipping...'

        # don't walk sub-directories unless -r flag supplied
        if not recurse:
            del dirs[:]
    return match_ids



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('target_dir',
                        help='directory to process .dem files from')
    parser.add_argument('-f', action='store_true',
                        help='force re-processing for matches already found in db')
    parser.add_argument('-r', action='store_true',
                        help='parse .dem files in sub-directories')
    args = parser.parse_args()

    process_replays(args.target_dir, args.r, args.f)

if __name__ == '__main__':
    main()
