from __future__ import absolute_import
from alacrity.mq.celery import celery
from alacrity.config.db import db, league_db
import alacrity.config.api as api

from alacrity.parsers.run_all import process_replays
from celery import chain, group
import requests
import re
import os
import tempfile
import bz2
tempfile.tempdir = os.path.join(tempfile.gettempdir(), "dota2replays")
if not os.path.exists(tempfile.tempdir):
    os.mkdir(tempfile.tempdir) # permissions determined by `umask`


@celery.task
def add(x, y):
    return x + y

@celery.task
def echo(x):
    print x
    return x

@celery.task
def workflow():
    print 'workflow'
    league_ids = get_valid_leagues()
    print 'league_ids: {}'.format(league_ids)
    for league_id in league_ids:
        print 'for league_id: {}'.format(league_id)
        match_ids = get_match_ids(league_id)
        print '  match_ids: {}'.format(match_ids)
        group([
            chain( \
                get_replay_url.s(x), \
                download_replay.s(), \
                parse_replay.s(), \
                delete_replay.s() \
            ) \
            for x in match_ids])()

@celery.task
def update_leagues():
    leagues = api.get_league_listing()['result']['leagues']
    # TODO: error-checking
    accessible_leagues = api.accessible_leagues
    for league in leagues:
        # accessible = free/open or the ticket is bought on the api account
        league['accessible'] = league['leagueid'] in accessible_leagues
        league_db.update({"leagueid": league['leagueid']}, {'$setOnInsert': league}, upsert=True)

@celery.task
def get_valid_leagues():
    """Valid = current in-progress leagues that are accessible (see config.cfg)"""
    print 'get_valid_leagues'
    return api.accessible_leagues

@celery.task
def get_match_ids(league_id):
    """Returns a list of all the ids for matches that aren't in the database"""
    # TODO: cache this call or maintain a separate collection? maybe it's fast b/c index
    print 'get_match_ids'
    cur_match_ids = set(db.distinct('match_id'))

    matches = []
    resp = api.get_match_history(league_id=league_id)[]
    if resp and resp['result']['status'] == 1:
        matches.extend(resp['result']['matches'])
        while resp['result']['results_remaining'] > 0:
            resp = api.get_match_history(league_id=league_id, start_at_match_id=matches[-1]['match_id'])[]
            if resp and resp['result']['status'] == 1:
                matches.extend(resp['result']['matches'][1:])
    else:
        raise Exception('API response failed, resp: {}'.format(resp))

    # TODO: better error-checking
    league_match_ids = set(match['match_id'] for match in matches)

    match_ids = league_match_ids - cur_match_ids

    # instead of returning match_ids, does this .apply_async to the whole workflow?
    # group(get_replay_url.s(m) for m in match_ids) | blah
    return match_ids

replayurl_regex = re.compile(r"http.*?\.dem\.bz2")
@celery.task
def get_replay_url(matchid):
    """Returns the replay url from the matchurls tool for the given matchid"""
    r = requests.get('http://localhost:3100/tools/matchurls', params={'matchid': matchid})
    match = replayurl_regex.search(r.text)
    if match:
        print 'replay url: {}'.format(match.group(0))
        return match.group(0)
    else:
        print 'no replay url found'
        # error handling: read the page to see what error was?
        pass

replayfile_regex = re.compile(r"\/(\d+)_")
@celery.task
def download_replay(replay_url):
    """Returns the path of the replay file downloaded from the given url"""
    replay_file = replayfile_regex.search(replay_url).group(1) + ".dem"

    #print 'HARDCODED REPLAY URL'
    #replay_url = "http://localhost:8000/271145478_239284874.dem.bz2"

    # http://stackoverflow.com/a/16696317/751774
    # replay will be downloaded to /tmp/dota2replays/replay_file on linux
    tmpdir = tempfile.mkdtemp(dir=tempfile.tempdir)
    replay_path = os.path.join(tmpdir, replay_file)

    r = requests.get(replay_url, stream=True)
    unzipper = bz2.BZ2Decompressor()
    with open(replay_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(unzipper.decompress(chunk))
                f.flush()
    print 'replay downloaded to: {}'.format(replay_path)
    return replay_path

@celery.task
def parse_replay(replay_path):
    """Runs parsers on the given replay (which output a json file to datastore)"""
    # run single concatenated parser

    process_replays(os.path.dirname(replay_path))
    return replay_path

@celery.task
def delete_replay(replay_path):
    """Removes the replay file and directory from the filesystem"""
    os.remove(replay_path)
    print 'removed replay file from: {}'.format(replay_path)
    os.rmdir(os.path.dirname(replay_path))
    print 'removed containing tmp directory: {}'.format(os.path.dirname(replay_path))
    return True
