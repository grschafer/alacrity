from ConfigParser import ConfigParser
from urllib2 import urlopen
import os
try: import simplejson as json
except ImportError: import json

_config = ConfigParser()
_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.cfg')
_config.read(_config_path)

def _get_api_key():
    return _config.get('api', 'key')

api_key = _get_api_key()

def get_match_details(match_id):
    url = 'http://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v1?key={}&match_id={}'.format(api_key, match_id)
    resp = urlopen(url)
    # TODO: error checking
    body = resp.read()
    match = json.loads(body)['result']
    return match

