from ConfigParser import ConfigParser
import requests
import os
try: import simplejson as json
except ImportError: import json

_config = ConfigParser()
_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.cfg')
_config.read(_config_path)

def _get_api_key():
    return _config.get('api', 'key')

api_key = _get_api_key()

accessible_leagues = json.loads(_config.get('api', 'accessible_leagues'))

MATCH_DETAILS_URL = 'http://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v1?key={}'.format(api_key)
def get_match_details(match_id):
    """See http://wiki.teamfortress.com/wiki/WebAPI/GetMatchDetails"""
    r = requests.get(MATCH_DETAILS_URL, params={'match_id': match_id})
    # TODO: error checking
    return r.json()

MATCH_HISTORY_URL = 'http://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v1?key={}'.format(api_key)
def get_match_history(**kwargs):
    """See http://wiki.teamfortress.com/wiki/WebAPI/GetMatchHistory"""
    r = requests.get(MATCH_HISTORY_URL, params=kwargs)
    return r.json()

LEAGUE_LISTING_URL = 'http://api.steampowered.com/IDOTA2Match_570/GetLeagueListing/v1?key={}'.format(api_key)
def get_league_listing():
    """See http://wiki.teamfortress.com/wiki/WebAPI/GetLeagueListing"""
    r = requests.get(LEAGUE_LISTING_URL, params={'language': 'en'})
    return r.json()
