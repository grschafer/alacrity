import pymongo
from ConfigParser import ConfigParser
import os


_config = ConfigParser()
_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.cfg')
_config.read(_config_path)

def _get_mongo_connection():
    db_server = (_config.get('db', 'host'), _config.getint('db', 'port'))
    db_name = _config.get('db', 'db_name')
    match_collection = _config.get('db', 'match_collection')
    league_collection = _config.get('db', 'league_collection')
    client = pymongo.mongo_client.MongoClient(*db_server)
    db = client[db_name]
    db[match_collection].ensure_index('match_id', pymongo.ASCENDING)
    db[league_collection].ensure_index('leagueid', pymongo.ASCENDING)
    return db

_db = _get_mongo_connection()
db = _db[_config.get('db', 'match_collection')]
league_db = _db[_config.get('db', 'league_collection')]
