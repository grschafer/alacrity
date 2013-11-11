from __future__ import absolute_import
from alacrity.mq.celery import celery
from alacrity.config.db import db
import alacrity.config.api as api


@celery.task
def add(x, y):
    return x + y

@celery.task
def get_match_ids():
    """Returns a list of all the ids for matches that aren't in the database"""
    matchids = []
    return matchids

@celery.task
def get_replay_url(matchid):
    """Returns the replay url from the matchurls tool for the given matchid"""
    replay_urls = []
    return replay_urls

@celery.task
def download_replay(replay_url):
    """Returns the path of the replay file downloaded from the given url"""
    replay_file = None
    return replay_file

@celery.task
def parse_replay(replay_file):
    """Runs parsers on the given replay (which output a json file to datastore)"""
    # run parsers
    return replay_file

@celery.task
def delete_replay(replay_file):
    """Removes the replay file from the filesystem"""
    return True
