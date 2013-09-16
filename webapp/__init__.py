#!/usr/bin/python

from flask import Flask, g
import pymongo

app = Flask(__name__)
app.config.from_pyfile('webapp.cfg')

def get_db():
    host, port = app.config['DATABASE'].values()
    client = pymongo.mongo_client.MongoClient(host, int(port))
    db = client[app.config['DB_NAME']]
    coll = db[app.config['COL_NAME']]
    return coll
db = get_db()

import webapp.views

