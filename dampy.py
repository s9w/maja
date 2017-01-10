import asyncio
import json
import logging
import time
import sqlite3
import webbrowser
from flask import Flask, render_template, url_for, request
import threading

import reddit, stackexchange, hackernews


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
        else:
            return ""

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
    conn = sqlite3.connect("db.sqlite", check_same_thread=False)
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


def make_template_data():
    template_data = {
        "reddit": [],
        "SE": []
    }

    for type in ["reddit", "SE"]:
        cursor.execute('SELECT DISTINCT subtype FROM categories WHERE type = ?', [type])
        subtypes = [item[0] for item in cursor.fetchall()]

        for subtype in subtypes:
            cursor.execute(
                'SELECT DISTINCT score, comments, title, link_in, ifnull(link_out, link_in), date, type, subtype FROM posts JOIN categories '
                'ON posts.category_id = categories.category_id '
                'WHERE read = 0 AND categories.type=? AND categories.subtype = ?'
                'ORDER BY "date" DESC ', [type, subtype])
            template_data[type].append({
                "subtype": subtype,
                "posts": cursor.fetchall()
            })
    cursor.execute(
        'SELECT DISTINCT score, comments, title, link_in, ifnull(link_out, link_in), date, type, subtype FROM posts JOIN categories '
        'ON posts.category_id = categories.category_id '
        'WHERE read = 0 AND categories.type=? AND categories.subtype = ?'
        'ORDER BY "date" DESC ', ["HN", ""])
    template_data["HN"] = cursor.fetchall()
    return template_data


def run_jobs():
    jobs_by_type, job_types = parse_jobs()
    update_categories(conn, cursor, job_types)
    for job_type, jobs in jobs_by_type.items():
        if job_type == "SE":
            pass
            stackexchange.run_jobs(conn, cursor, jobs, se_conf, se_token)

        elif job_type == "reddit":
            reddit.run_jobs(conn, cursor, jobs, reddit_token)

        elif job_type == "HN":
            hackernews.run_jobs(conn, cursor, jobs)


if __name__ == '__main__':
    # setup logging
    logging.basicConfig(level=logging.INFO)

    # mute noise packages
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    se_conf = {
        "client_id": "8691",

        # app key. "This is not considered a secret, and may be
        # safely embed in client side code or distributed binaries."
        "key": "bVsLGOdziqDVuvgu974HWQ(("
    }

    se_token = se_load_token()

    # get one reddit API token initially. Will auto-renew if expires (after 60 minutes)
    reddit_token = reddit.get_token()

    # open/create database
    conn, cursor = init_db()

    # API calls will run on a different thread to not block the server
    threads = []

    app = Flask(__name__)

    @app.route('/scrape')
    def start_scraping():
        t = threading.Thread(target=run_jobs)
        threads.append(t)
        t.start()
        return ""

    @app.route('/mark_read')
    def mark_read():
        # set read to 1, null unnecessary info to save space
        cursor.execute(
            'UPDATE posts SET read = 1, link_in = NULL, link_out = NULL, title = NULL '
            'WHERE category_id = (SELECT category_id from categories WHERE type = ? AND subtype = ?) AND date <= ?',
            [request.args.get("type"), request.args.get("subtype"), request.args.get("timestamp")]
        )
        conn.commit()
        return ""

    @app.route('/')
    def html_root():
        return render_template('dampy.html', data=make_template_data())

    t = threading.Thread(target=app.run)
    threads.append(t)
    t.start()

    # conn.close()
