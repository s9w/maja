import json
import logging
import pprint
import sqlite3
import webbrowser

import praw
import sqlalchemy
from sqlalchemy import Integer, String, Table
from sqlalchemy import schema

import reddit, stackexchange


def se_get_token(se_conf):
    base_url = "https://stackexchange.com/oauth/dialog"
    success_url = "https://stackexchange.com/oauth/login_success"
    url = "{}?client_id={}&scope=no_expiry&redirect_uri={}".format(
        base_url, se_conf["client_id"], success_url)
    webbrowser.open(url)


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
            stackexchange.run_jobs(conn, cursor, jobs, se_conf, se_token)

        elif job_type == "reddit":
            reddit.run_jobs(conn, cursor, jobs, reddit_token)

    conn.close()
