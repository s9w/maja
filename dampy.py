import json
import sqlalchemy
from sqlalchemy import Column, Integer, String, Table
from sqlalchemy import schema, types
from sqlalchemy.sql import select
import records
import webbrowser
import time

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
    # load from json job file
    try:
        with open('jobs.json') as data_file:
            json_jobs = json.load(data_file)
    except FileNotFoundError:
        json_jobs = []

    # group jobs by type
    jobs = {
        "SE": [],
        "reddit": [],
        "HN": []
    }
    for job in json_jobs:
        jobs[job["type"]].append(job)

    return jobs


def run_jobs_se(conn, jobs, se_conf, se_token):
    now = arrow.utcnow()
    earlier = now.replace(months=-1)
    print("earlier.timestamp", earlier.timestamp)

    def make_request(max):
        # prepare request parameters
        payload = (
            ("site", job["site"]),
            ("client_id", se_conf["client_id"]),
            ("key", se_conf["key"]),
            ("access_token", se_token),
            ("fromdate", earlier.timestamp),
            ("sort", "votes"),
            ("min", job["score"]),
            ("pagesize", 20)
        )

        # pagination, if previous request did not get all results
        if max is not None:
            payload += ("max", max),

        # make request
        api_url = 'https://api.stackexchange.com/2.2/questions'
        r = requests.get(api_url, params=payload)
        print("url", r.url)
        res_json = r.json()
        if r.status_code != requests.codes.ok:
            print("status code not OK!", r.status_code)


        # lowest score of all questions, needed for pagination
        if res_json["has_more"]:
            min_score = res_json["items"][-1]["score"]
        else:
            min_score = 999

        return res_json["items"], \
               min_score, \
               res_json["has_more"], \
               res_json.get("backoff", -1), \
               res_json["quota_remaining"]

    backoff = -1
    for job in jobs:
        print("  new job: ", job.items())
        done = False
        max_score = None
        while not done:
            if backoff > 0:
                print("sleeping {} seconds...".format(backoff), end="", flush=True)
                time.sleep(backoff)
                print(" done")
            items, min_score, has_more, backoff, quota_remaining = make_request(max_score)

            done = not has_more
            print("max_score:", max_score, ",  len:", len(items), ", done:", done, ", backoff:", backoff, quota_remaining)

            # same-score answers could be missing
            max_score = min_score


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

    return conn


if __name__ == '__main__':
    if __debug__:
        print("ja")
    else:
        print("nein")

    se_conf = {
        "client_id": "8691",

        # app key. "This is not considered a secret, and may be
        # safely embed in client side code or distributed binaries."
        "key": "bVsLGOdziqDVuvgu974HWQ(("
    }
    se_token = se_load_token()

    # open/create database
    conn = init_db()

    # jobs
    # jobs = parse_jobs()
    # for job_type, jobs in jobs.items():
    #     if job_type == "SE":
    #         run_jobs_se(conn, jobs, se_conf, se_token)

    # se_test(se_conf, se_token)
