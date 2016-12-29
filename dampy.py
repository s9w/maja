import json
import pprint
import uuid

import praw
import sqlalchemy
from sqlalchemy import Column, Integer, String, Table
from sqlalchemy import schema, types
from sqlalchemy.sql import select
import webbrowser
import logging
import time

import requests
import arrow


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

def reddit_get_token():
    # Application Only OAuth
    client_id = "IUrObKU-ORiL1g"
    endpoint = "https://www.reddit.com/api/v1/access_token"
    device_id = "6e6cc493-69a4-483e-a554-d4d2cb963fe1"
    headers = {'user-agent': "windows:dampy:v0.1 (by /u/SE400PPp)"}
    post_data = {
        'grant_type': 'https://oauth.reddit.com/grants/installed_client',
        "device_id": device_id
    }
    r = requests.post(endpoint, data=post_data, headers=headers,
                      auth=(client_id, ""))
    print(r.text)

    token = r.json()["access_token"]
    print("token", token)
    return token


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


def insert_to_db(posts, conn, items, subtype):
    rows = []
    for item in items:
        rows.append({
            "id": item["question_id"],
            "type": "SE",
            "subtype": subtype,
            "link_in": item["link"],
            "score": item["score"],
            "title": item["title"],
            "comments": item["answer_count"]
        })

    conn.execute(posts.insert().prefix_with("OR REPLACE"), rows)


def run_jobs_se(posts, conn, jobs, se_conf, se_token):
    now = arrow.utcnow()
    earlier = now.replace(months=-1)
    logging.info("earlier.timestamp: {}".format(earlier.timestamp))

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
                insert_to_db(posts, conn, items, subtype=job["site"])

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
                  schema.Column('link_out', String),
                  schema.Column('link_in', String, nullable=False),
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
    # conn.execute(posts.insert().prefix_with("OR REPLACE"), [
    #     {"id": "3", "type": "reddit", "subtype": "cpp", "link1": "test1"},
    #     {"id": "4", "type": "reddit", "subtype": "python", "link1": "test2"},
    #     {"id": "4", "type": "reddit", "subtype": "python", "link1": "test3"}
    # ])

    # select
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

    # reddit_token = reddit_get_token()
    reddit_token = "5lklrbHkIoTeMUhkrxItCLD_xKw"
    praw_test(reddit_token)

    # open/create database
    # posts, conn = init_db()

    # jobs
    # jobs = parse_jobs()
    # for job_type, jobs in jobs.items():
    #     if job_type == "SE":
    #         run_jobs_se(posts, conn, jobs, se_conf, se_token)

