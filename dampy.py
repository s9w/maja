import json
import logging
import pprint
import sqlite3
import webbrowser
from flask import Flask, render_template


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


def get_posts(type, subtype):
    pass


def parse_jobs():
    def get_subtype(job):
        if job["type"] == "SE":
            return job["site"]
        elif job["type"] == "reddit":
            return job["subreddit"]

    # load from json job file
    try:
        with open('jobs.json') as data_file:
            json_jobs = json.load(data_file)
    except FileNotFoundError:
        json_jobs = []

    # group jobs by type
    jobs_by_type = {
        "SE": [],
        "reddit": [],
        "HN": []
    }
    job_types = []
    for job in json_jobs:
        type = job["type"]
        subtype = get_subtype(job)
        jobs_by_type[type].append(job)

        job_types.append((type, subtype))

    return jobs_by_type, job_types


def init_db():
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()

    cursor.execute(
        'CREATE TABLE IF NOT EXISTS categories ('
        'category_id INTEGER PRIMARY KEY, '
        'type STRING, '
        'subtype STRING, '
        'UNIQUE(type, subtype) ON CONFLICT IGNORE ) ')

    cursor.execute(
        'CREATE TABLE IF NOT EXISTS "posts" ('
        '"id" "STRING", '
        '"category_id" "INTEGER", '
        '"link_in" "STRING", '
        '"link_out" "STRING", '
        '"title" "STRING", '
        '"score" "INTEGER", '
        '"comments" "INTEGER", '
        '"date" "INTEGER", '
        '"read" "INTEGER" DEFAULT 0, '
        'PRIMARY KEY("id", "category_id"), '
        'FOREIGN KEY(category_id) REFERENCES categories(category_id)'
        ')')

    conn.commit()
    return conn, cursor


def update_categories(conn, cursor, job_types):
    cursor.executemany(
        'INSERT INTO categories(type, subtype)'
        'VALUES (?, ?)', job_types
    )
    conn.commit()


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

    reddit_token = "XYyjumkNnoRo5EZoxXEZRSHFob8" # 9:47
    # reddit_token = reddit.get_token()
    # reddit_test(reddit_token)
    # praw_test(reddit_token)

    # open/create database
    conn, cursor = init_db()

    # jobs
    jobs_by_type, job_types = parse_jobs()
    update_categories(conn, cursor, job_types)

    # for job_type, jobs in jobs_by_type.items():
    #     if job_type == "SE":
    #         stackexchange.run_jobs(conn, cursor, jobs, se_conf, se_token)
    #
    #     elif job_type == "reddit":
    #         reddit.run_jobs(conn, cursor, jobs, reddit_token)


    template_data = {
        "reddit": [],
        "SE": []
    }

    cursor.execute(
            'SELECT DISTINCT * FROM posts WHERE category_id = (SELECT category_id from categories WHERE type="reddit" AND subtype = ?)', ["programming"])

    names = list(map(lambda x: x[0], cursor.description))
    print(names)

    cursor.execute('SELECT DISTINCT subtype FROM categories WHERE type = "reddit"')
    subreddits = [item[0] for item in cursor.fetchall()]

    for type in ["reddit", "SE"]:
        cursor.execute('SELECT DISTINCT subtype FROM categories WHERE type = ?', [type])
        subtypes = [item[0] for item in cursor.fetchall()]

        for subtype in subtypes:
            cursor.execute(
                'SELECT DISTINCT * FROM posts '
                'WHERE category_id = (SELECT category_id from categories WHERE type=? AND subtype = ?)'
                'ORDER BY "date" DESC ', [type, subtype])
            template_data["reddit"].append({
                "subreddit": subtype,
                "posts": cursor.fetchall()
            })


    app = Flask(__name__)
    @app.route('/')
    def html_root():
        return render_template('dampy.html', data=template_data)
    app.run()

    conn.close()
