#!/usr/bin/python
# -*- coding: utf-8 -*-

from tarrasque import *
import os
import argparse
import pdb
import traceback

# helpers
from alacrity.config.db import db
import alacrity.config.api as api
from parser import Parser
import preparsers

from ward_map import WardParser
from buyback import BuybackParser
from gold_xp_graphs import GraphParser
from hero_position import PositionParser
from kill_list import KillParser
from roshan import RoshanParser
from runes import RuneParser
from scoreboard import ScoreboardParser

# __subclasses__() will contain all the subclasses of the
# base Parser class that are imported in this scope
parser_classes = Parser.__subclasses__()
preparser_classes = preparsers.Preparser.__subclasses__()

def parse_replay(replay):
    # get general pre-parsing info (e.g. player-hero-team-name mappings)
    # by iterating through replay's full-ticks first
    # this info is available to parsers because preparsers are singletons
    preparsers = []
    for preparser in preparser_classes:
        preparsers.append(preparser(replay))
    for tick in replay.iter_full_ticks(start="pregame", end="postgame"):
        print 'tick: {}'.format(tick)
        for preparser in preparsers:
            preparser.parse(replay)

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

    result = {}
    for parser in parsers:
        result.update(parser.results)
    return result


def endswith(array, ending):
    for x in array:
        if x.endswith(ending):
            yield x

def process_replays(directory, recurse=False, force=False):
    for root, dirs, files in os.walk(directory):
        for fname in endswith(files, '.dem'):
            path = os.path.join(root, fname)
            print 'processing match from {}'.format(path)

            replay = StreamBinding.from_file(path, start_tick=0)
            match_id = replay.info.match_id
            print '  match id {}'.format(match_id)

            if force or db.find_one({'match_id': match_id}) is None:
                match = db.find_one({'match_id': match_id}) or {'match_id': match_id}
                #match.update(api.get_match_details(match_id))
                #print '  match details: {} vs {}, radiant_win: {}'.format(match.get('radiant_name', ''), match.get('dire_name', ''), match['radiant_win'])
                parsed = parse_replay(replay)
                match.update(parsed)
                result = db.update({'match_id': match_id}, match, upsert=True)
                print '  result: {}'.format(result)
            else:
                print '  match already exists in database, skipping...'

        # don't walk sub-directories unless -r flag supplied
        if not recurse:
            del dirs[:]



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
