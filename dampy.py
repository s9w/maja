import json
import sqlalchemy
from sqlalchemy import Column, Integer, String, Table
from sqlalchemy import schema, types
from sqlalchemy.sql import select
import records
import webbrowser

import requests
import arrow


def se_get_token(se_conf):
    base_url = "https://stackexchange.com/oauth/dialog"
    success_url = "https://stackexchange.com/oauth/login_success"
    url = "{}?client_id={}&scope=no_expiry&redirect_uri={}".format(
        base_url, se_conf["se_client_id"], success_url)
    webbrowser.open(url)


def se_load_token():
    with open('secrets.json') as data_file:
        data = json.load(data_file)
    return data.get("se_access_token", "")


def se_test(se_conf, se_token):
    now = arrow.utcnow()
    earlier = now.replace(months=-1)
    print(earlier)
    print(earlier.timestamp)

    payload = (
        ("site", "tex"),
        ("client_id", se_conf["client_id"]),
        ("key", se_conf["key"]),
        ("access_token", se_token),
        ("fromdate", earlier.timestamp),
        ("sort", "votes"),
        ("min", 60)
    )
    r = requests.get('https://api.stackexchange.com/2.2/questions', params=payload)
    print("url", r.url)
    print(r)
    res_json = r.json()
    backoff_time = res_json.get("backoff", -1)
    print(res_json)
    print("backoff", backoff_time)


def parse_jobs():
    jobs = []
    with open('jobs.json') as data_file:
        jobs = json.load(data_file)
    return jobs


def init_db():
    engine = sqlalchemy.create_engine('sqlite:///db.db', echo=False)
    metadata = sqlalchemy.MetaData()

    posts = Table('posts', metadata,
                  schema.Column('id', String, primary_key=True, unique=False),
                  schema.Column('type', String, primary_key=True),
                  schema.Column('subtype', String, primary_key=True),
                  schema.Column('link1', String),
                  schema.Column('link2', String, nullable=False),
                  schema.Column('score', Integer, nullable=False),
                  schema.Column('title', String, nullable=False),
                  schema.Column('comments', Integer, nullable=False)
                  )

    metadata.create_all(engine)

    # insert single
    conn = engine.connect()
    # ins = posts.insert().values(id="1", type="HN", subtype="")
    # result = conn.execute(ins)
    # ins = posts.insert().values(id="2", type="reddit", subtype="programming")
    # result = conn.execute(ins)

    # insert multiple
    # conn.execute(posts.insert(), [
    #     {"id": "3", "type": "reddit", "subtype": "cpp"},
    #     {"id": "4", "type": "reddit", "subtype": "python"},
    #     {"id": "4", "type": "reddit", "subtype": "archer"}
    # ])

    # select
    s = select([posts])
    result = conn.execute(s)
    for row in result:
        print(row, row["id"], row[posts.c.id])
    result.close()

    # select adv
    s = select([posts.c.id, posts.c.type])
    result = conn.execute(s)
    for row in result:
        print(row)


if __name__ == '__main__':
    se_conf = {
        "client_id": "8691",

        # app key. "This is not considered a secret, and may be
        # safely embed in client side code or distributed binaries."
        "key": "bVsLGOdziqDVuvgu974HWQ(("
    }

    # open/create database
    init_db()

    # jobs
    # jobs = parse_jobs()
    # for job in jobs:
    #     print("type", job["type"])
    #
    # print("version", sqlalchemy.__version__ )

    # se_token = se_load_token()
    # se_test(se_conf, se_token)
