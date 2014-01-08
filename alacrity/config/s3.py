from ConfigParser import ConfigParser
import boto
import os
try: import simplejson as json
except ImportError: import json

_config = ConfigParser()
_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.cfg')
_config.read(_config_path)

def upload(key, match_data):
    """Uploads the match_data (param #2) to s3 under the given path (param #1)"""
    access_key = _config.get('s3', 'access_key')
    secret_key = _config.get('s3', 'secret_key')
    bucket = _config.get('s3', 'bucket')

    conn = boto.connect_s3(access_key, secret_key)
    b = conn.get_bucket(bucket)
    k = boto.s3.key.Key(b)
    k.key = str(key) + '.json' # name of file in bucket
    k.set_contents_from_string(json.dumps(match_data))
    k.set_metadata('Content-Type', 'application/json')
    k.set_acl('public-read')
    url = k.generate_url(expires_in=0, query_auth=False, force_http=True)
    return url

