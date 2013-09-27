import pymongo
from ConfigParser import ConfigParser
import os


_config = ConfigParser()
_config_path = os.path.join('config.cfg')
_config.read(_config_path)

def _get_mongo_connection():
    db_server = (_config.get('db', 'host'), _config.getint('db', 'port'))
    db_name = _config.get('db', 'db_name')
    collection_name = _config.get('db', 'collection_name')
    client = pymongo.mongo_client.MongoClient(*db_server)
    db = client[db_name][collection_name]
    db.ensure_index('match_id', pymongo.ASCENDING)
    return db

db = _get_mongo_connection()
