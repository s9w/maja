import json
import logging
import pprint
import sqlite3
import time
import webbrowser

import arrow
import praw
import requests
import sqlalchemy
from sqlalchemy import Integer, String, Table
from sqlalchemy import schema

# from reddit import run_jobs_reddit
import reddit


def se_get_token(se_conf):
    base_url = "https://stackexchange.com/oauth/dialog"
    success_url = "https://stackexchange.com/oauth/login_success"
    url = "{}?client_id={}&scope=no_expiry&redirect_uri={}".format(
        base_url, se_conf["client_id"], success_url)
    webbrowser.open(url)


# def reddit():
#     base_url = "https://www.reddit.com/api/v1/authorize"
#     client_id = "IUrObKU-ORiL1g"
#     state = "111"
#     redirect_uri = "http://127.0.0.1:65010/authorize_callback"
#     url = "{}?client_id={}&response_type=code&state={}&redirect_uri={}&duration=permanent&scope=identity".format(
#         base_url, client_id, state, redirect_uri)
#     webbrowser.open(url)

def praw_test(token):
    # installed: client_secret -> None
    # Read Only: no refresh_token

    client_id = "IUrObKU-ORiL1g"
    user_agent = "windows:dampy:v0.1 (by /u/SE400PPp)"
    uri = "http://127.0.0.1:65010/authorize_callback"
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=None,
        redirect_uri = uri,
        user_agent=user_agent
    )
    # print(reddit.auth.scopes())

    subreddit = reddit.subreddit('redditdev')
    for submission in subreddit.hot(limit=1):
        # print(submission.title)
        pprint.pprint(vars(submission))


def se_load_token():
    with open('secrets.json') as data_file:
        data = json.load(data_file)
    return data.get("se_access_token", "")


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


def run_jobs_se(conn, cursor, jobs, se_conf, se_token):
    now = arrow.utcnow()
    earlier = now.replace(months=-1)
    logging.info("earlier.timestamp: {}".format(earlier.timestamp))

    def insert_to_db(items, subtype):
        rows = []
        for item in items:
            rows.append((
                item["question_id"],
                "SE",
                subtype,
                item["link"],
                item["title"],
                item["score"],
                item["answer_count"]
            ))

        cursor.executemany(
            'INSERT OR REPLACE INTO posts(id, type, subtype, link_in, title, score, comments)'
            'VALUES (?, ?, ?, ?, ?, ?, ?)', rows
        )
        conn.commit()

    def make_request(job, max):
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

        if job.get("tags"):
            payload += ("tagged", job["tags"]),

        # pagination, if previous request did not get all results
        if max is not None:
            payload += ("max", max),

        # make request
        api_url = 'https://api.stackexchange.com/2.2/questions'
        r = requests.get(api_url, params=payload)
        logging.debug("url: {}".format(r.url))
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
            items, min_score, has_more, backoff, quota_remaining = make_request(job, max_score)
            if len(items) > 0:
                insert_to_db(items, subtype=job["site"])

            done = not has_more
            print("max_score:", max_score, ",  len:", len(items), ", done:", done, ", backoff:", backoff, quota_remaining)

            # same-score answers could be missing
            max_score = min_score

def init_db():
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()

    cursor.execute(
        'CREATE TABLE IF NOT EXISTS "posts" ('
        '"id" "STRING", '
        '"type" "STRING", '
        '"subtype" "STRING", '
        '"link_in" "STRING", '
        '"link_out" "STRING", '
        '"title" "STRING", '
        '"score" "INTEGER", '
        '"comments" "INTEGER", '
        '"read" "INTEGER" DEFAULT 0, '
        'PRIMARY KEY("id", "type", "subtype")'
        ')')

    # cursor.execute(
    #     'INSERT OR REPLACE INTO posts(id, type, subtype, score)'
    #     'VALUES (100, "reddit", "programming", 42)'
    # )
    #
    # cursor.execute(
    #     'INSERT OR REPLACE INTO posts(id, type, subtype, score)'
    #     'VALUES (100, "reddit", "programming", 43)'
    # )

    conn.commit()

    # conn.close()
    return conn, cursor

def db2():
    pass


def init_db_alchemy():
    engine = sqlalchemy.create_engine('sqlite:///db.db', echo=False)
    metadata = sqlalchemy.MetaData()

    posts = Table('posts', metadata,
                  schema.Column('id', String, primary_key=True, unique=False),
                  schema.Column('type', String, primary_key=True),
                  schema.Column('subtype', String, primary_key=True),
                  schema.Column('link_out', String),
                  schema.Column('link_in', String, nullable=False),
                  schema.Column('score', Integer, nullable=False),
                  schema.Column('title', String, nullable=False),
                  schema.Column('comments', Integer, nullable=False),
                  schema.Column('read', Integer, nullable=False)
                  )
    print(str(Table))

    metadata.create_all(engine)

    # insert single
    conn = engine.connect()
    # ins = posts.insert().values(id="1", type="HN", subtype="")
    # result = conn.execute(ins)
    # ins = posts.insert().values(id="2", type="reddit", subtype="programming")
    # result = conn.execute(ins)

    # # insert multiple
    # conn.execute(posts.insert().prefix_with("OR REPLACE"), [
    #     {"id": "3", "type": "reddit", "subtype": "cpp", "link1": "test1"},
    #     {"id": "4", "type": "reddit", "subtype": "python", "link1": "test2"},
    #     {"id": "4", "type": "reddit", "subtype": "python", "link1": "test3"}
    # ])

    # # select
    # s = select([posts])
    # result = conn.execute(s)
    # for row in result:
    #     print(row, row["id"], row[posts.c.id])
    # result.close()

    # select adv
    # s = select([posts.c.id, posts.c.type])
    # result = conn.execute(s)
    # for row in result:
    #     print(row)

    return posts, conn


if __name__ == '__main__':
    # setup logging
    logging.basicConfig(level=logging.INFO)
    # requests is a bit verbose
    logging.getLogger("requests").setLevel(logging.WARNING)

    se_conf = {
        "client_id": "8691",

        # app key. "This is not considered a secret, and may be
        # safely embed in client side code or distributed binaries."
        "key": "bVsLGOdziqDVuvgu974HWQ(("
    }
    # se_get_token(se_conf)

    se_token = se_load_token()

    reddit_token = "pBYAZ676Uy6VSIHV5d64bxWL2Bo" # 10:56
    # reddit_token = reddit.get_token()
    # reddit_test(reddit_token)
    # praw_test(reddit_token)

    # open/create database
    conn, cursor = init_db()

    # jobs
    jobs = parse_jobs()
    for job_type, jobs in jobs.items():
        if job_type == "SE":
            run_jobs_se(conn, cursor, jobs, se_conf, se_token)

        elif job_type == "reddit":
            reddit.run_jobs(conn, cursor, jobs, reddit_token)

    conn.close()
