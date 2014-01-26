from __future__ import absolute_import
from alacrity.mq.celery import celery
import alacrity.mq.celeryconfig as cfg
import alacrity.config as cfg_root
from alacrity.config.db import db, league_db, errorgame_db, userupload_db
import alacrity.config.api as api

#from alacrity.parsers.run_all import process_replays
from alacrity.parsers.all_in_one import process_replays
from celery import chain, group
from ConfigParser import ConfigParser
import celery.utils.mail as mail
import requests
import re
import os
import tempfile
import bz2
import time
tempfile.tempdir = os.path.join(tempfile.gettempdir(), "dota2replays")
if not os.path.exists(tempfile.tempdir):
    os.mkdir(tempfile.tempdir) # permissions determined by `umask`

_config = ConfigParser()
_config_path = os.path.join(os.path.dirname(os.path.realpath(cfg_root.__file__)), 'config.cfg')
_config.read(_config_path)

matchurls_host = _config.get('matchurls', 'host')
matchurls_port = _config.get('matchurls', 'port')
matchurls_url = "http://{}:{}/tools/matchurls".format(matchurls_host, matchurls_port)

# mailer configuration from celeryconfig.py
mailer = mail.Mailer(host=cfg.EMAIL_HOST,
                     port=cfg.EMAIL_PORT,
                     user=cfg.EMAIL_HOST_USER,
                     password=cfg.EMAIL_HOST_PASSWORD,
                     use_ssl=cfg.EMAIL_USE_SSL)
mail_sender = cfg.SERVER_EMAIL
email_subj_tmpl = "{hostname}: Your Request for Match {match_id} Fulfilled!"
email_body_tmpl = """
Your request to process match {match_id} has been fulfilled!

Please visit {match_url} to view your requested match.

Don't hesitate to contact me if anything has gone awry!

Cheers!
-Greg
"""
twitter_body_tmpl = "Match {match_id} has been processed! Please visit {match_url} to view."


import time

@celery.task
def add(x, y):
    print 'add {}+{}'.format(x,y)
    time.sleep(10)
    return x + y
@celery.task
def sub(x, y):
    print 'sub {}-{}'.format(x,y)
    time.sleep(10)
    return x - y
@celery.task
def mul(x, y):
    print 'mul {}*{}'.format(x,y)
    time.sleep(10)
    return x * y
@celery.task
def div(x, y):
    print 'div {}/{}'.format(x,y)
    time.sleep(10)
    return x / y
@celery.task
def xsum(args):
    print 'xsum {}'.format(args)
    time.sleep(10)
    return sum(args)

@celery.task
def echo(x):
    print x
    return x

@celery.task
def emit_list():
    return range(10)

@celery.task
def emit_list2(x):
    print 'emit_list2: {}'.format(x)
    if x%2 == 1:
        return [x, x+1, x+2]
    return [x, x/2]

@celery.task
def league_match_workflow():
    print 'workflow'
    league_ids = get_valid_leagues()
    print 'league_ids: {}'.format(league_ids)
    # convert for-loop to chunks?
    # http://docs.celeryproject.org/en/latest/userguide/canvas.html#chunks
    for league_id in league_ids:
        # TODO: break iterations of these for-loops into separate tasks?
        time.sleep(1) # only want to hit steam API once per second

        print 'for league_id: {}'.format(league_id)
        match_ids = get_match_ids(league_id)
        print '  match_ids: {}'.format(match_ids)
        for match_id in match_ids:
            chain( \
                get_replay_url.s((match_id, None)), \
                download_replay.s(), \
                parse_replay.s(), \
                delete_replay.s() \
            ).apply_async()


@celery.task
def user_replay_workflow():
    # also fetch user-uploaded replays
    user_uploaded = userupload_db.find()
    for match in user_uploaded:
        # if match requested by match_id
        if match.get('match_id') is not None:
            chain( \
                get_replay_url.s((match['match_id'], match['notif_key'])), \
                download_replay.s(), \
                parse_replay.s(), \
                delete_replay.s() \
            ).apply_async()
        # else match uploaded by user to s3 and we already have download url
        else:
            chain( \
                download_replay.s((match['url'], match['notif_key'])), \
                parse_replay.s(), \
                delete_replay.s() \
            ).apply_async()


@celery.task(rate_limit="1/m")
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
    # TODO: filter out leagues that have already completed
    return api.accessible_leagues

@celery.task(rate_limit="1/m")
def get_match_ids(league_id):
    """Returns a list of all the ids for matches that aren't in the database"""
    # TODO: cache this call or maintain a separate collection? maybe it's fast b/c index
    print 'get_match_ids'
    cur_match_ids = set(db.distinct('match_id'))
    errorgame_ids = set(errorgame_db.distinct('match_id'))

    matches = []
    resp = api.get_match_history(league_id=league_id)
    if resp and resp['result']['status'] == 1:
        matches.extend(resp['result']['matches'])
        while resp['result']['results_remaining'] > 0:
            time.sleep(1) # 1 call per second
            resp = api.get_match_history(league_id=league_id, start_at_match_id=matches[-1]['match_id'])
            if resp and resp['result']['status'] == 1:
                matches.extend(resp['result']['matches'][1:])
    else:
        raise Exception('API response failed, resp: {}'.format(resp))

    # TODO: better error-checking
    league_match_ids = set(match['match_id'] for match in matches)

    match_ids = league_match_ids - cur_match_ids - errorgame_ids

    # instead of returning match_ids, does this .apply_async to the whole workflow?
    # group(get_replay_url.s(m) for m in match_ids) | blah
    return match_ids

replayurl_regex = re.compile(r"http.*?\.dem\.bz2")
@celery.task(rate_limit="1/m")
def get_replay_url(match_notif):
    matchid, notif_key = match_notif
    """Returns the replay url from the matchurls tool for the given matchid"""
    r = requests.get(matchurls_url, params={'matchid': matchid})
    match = replayurl_regex.search(r.text)
    if match:
        print 'replay url: {}'.format(match.group(0))
        return match.group(0), notif_key
    else:
        print 'no replay url found'
        # error handling: read the page to see what error was?
        pass

# %2F is the urlencoded version of forward slash /
replayfile_regex = re.compile(r"(\/|%2F)(\d+)[_.]")
@celery.task(rate_limit="1/m")
def download_replay(url_notif):
    replay_url, notif_key = url_notif
    """Returns the path of the replay file downloaded from the given url"""
    replay_file = replayfile_regex.search(replay_url).group(2) + ".dem"

    #print 'HARDCODED REPLAY URL'
    #replay_url = "http://localhost:8000/271145478_239284874.dem.bz2"

    # http://stackoverflow.com/a/16696317/751774
    # replay will be downloaded to /tmp/dota2replays/tmpdir/replay_file on linux
    replay_path = os.path.join(tempfile.tempdir, replay_file)
    # if replay file already exists, don't download it again
    if os.path.isfile(replay_path):
        return replay_path, notif_key

    # replays from valve are bz2 compressed
    # replays from aws are uncompressed and use this NoopDecompressor
    class NoopDecompressor(object):
        def decompress(self, chunk):
            return chunk

    r = requests.get(replay_url, stream=True)
    unzipper = bz2.BZ2Decompressor() if replay_url.endswith('.bz2') else NoopDecompressor()
    with open(replay_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(unzipper.decompress(chunk))
                f.flush()
    print 'replay downloaded to: {}'.format(replay_path)
    return replay_path, notif_key

@celery.task(rate_limit="1/m")
def parse_replay(path_notif, **kwargs):
    replay_path, notif_key = path_notif
    """Runs parsers on the given replay (which output a json file to datastore)"""
    # run single concatenated parser

    match_ids = process_replays(os.path.dirname(replay_path), **kwargs)
    if notif_key is not None and len(match_ids) > 0:
        notify_requester.delay((match_ids[0], notif_key))
    return replay_path

@celery.task
def notify_requester(match_notif):
    match_id, notif_key = match_notif
    notify_request = userupload_db.find_one({'notif_key': notif_key})
    if notify_request is None:
        return

    # limit access to match to requesting user and remove from userupload db
    db.update({'match_id': match_id}, {'$set': {'requester': notify_request['requesting_user']}})
    userupload_db.remove({'notif_key': notif_key})

    if 'notif_method' not in notify_request:
        return

    notify_method = notify_request['notif_method'].lower()
    to_addr = notify_request['notif_address']
    match_url = "http://{}/matches/{}".format(_config.get('web', 'hostname').strip('"'), match_id)

    if notify_method == "email":
        subj_text = email_subj_tmpl.format(hostname=_config.get('web', 'hostname'), match_id=match_id)
        body_text = email_body_tmpl.format(match_id=match_id, match_url=match_url)
        msg = mail.Message(to=to_addr, sender=mail_sender, subject=subj_text, body=body_text)
        mailer.send(msg)
    elif notify_method == "twitter":
        msg_text = twitter_body_tmpl.format(match_id=match_id, match_url=match_url)
        username = to_addr if to_addr.startswith('@') else "@{}".format(to_addr)
        # TODO: implement twitter messaging
        raise NotImplementedError()


@celery.task
def delete_replay(replay_path):
    """Removes the replay file and directory from the filesystem"""
    os.remove(replay_path)
    print 'removed replay file from: {}'.format(replay_path)
    return True
