import asyncio
import json
import logging
import time
import sqlite3
import webbrowser
from flask import Flask, render_template, url_for, request
import threading
from datetime import datetime

from sources import reddit, stackexchange, hackernews, fourchan


def se_load_token():
    with open('secrets.json') as data_file:
        data = json.load(data_file)
    return data.get("se_access_token", "")


def parse_jobs():
    def get_subtype(job):
        if job["type"] == "SE":
            return job["site"]
        elif job["type"] == "reddit":
            return job["subreddit"]
        elif job["type"] == "4chan":
            return job["board"]
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
        "HN": [],
        "4chan": []
    }
    job_types = []
    for job in json_jobs:
        job_type = job["type"]
        subtype = get_subtype(job)
        jobs_by_type[job_type].append(job)

        job_types.append((job_type, subtype))

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
    conn_web = sqlite3.connect("db.sqlite", check_same_thread=False)
    return conn, conn_web


def update_categories(conn, job_types):
    cursor = conn.cursor()
    cursor.executemany(
        'INSERT INTO categories(type, subtype)'
        'VALUES (?, ?)', job_types
    )
    conn.commit()


def make_template_data(conn):
    def sanitize_type(site_type):
        if site_type == "4chan":
            return "fourchan"
        return site_type

    template_data = {}

    cursor = conn.cursor()

    for site_type in ["reddit", "SE", "4chan"]:
        cursor.execute('SELECT DISTINCT subtype FROM categories WHERE type = ?', [site_type])
        subtypes = [item[0] for item in cursor.fetchall()]

        for subtype in subtypes:
            cursor.execute(
                'SELECT DISTINCT score, comments, title, link_in, ifnull(link_out, link_in), date, type, subtype, categories.category_id FROM posts JOIN categories '
                'ON posts.category_id = categories.category_id '
                'WHERE read = 0 AND categories.type=? AND categories.subtype = ?'
                'ORDER BY "date" DESC ', [site_type, subtype])
            template_data.setdefault(sanitize_type(site_type), []).append({
                "subtype": subtype,
                "posts": cursor.fetchall()
            })
    cursor.execute(
        'SELECT DISTINCT score, comments, title, link_in, ifnull(link_out, link_in), date, type, subtype, categories.category_id FROM posts JOIN categories '
        'ON posts.category_id = categories.category_id '
        'WHERE read = 0 AND categories.type=? AND categories.subtype = ?'
        'ORDER BY "date" DESC ', ["HN", ""])
    template_data["HN"] = cursor.fetchall()
    return template_data


def run_jobs(conn, se_conf, tokens):
    logging.info("scraping started at {}".format(time.ctime()))
    jobs_by_type, job_types = parse_jobs()
    update_categories(conn, job_types)
    for job_type, jobs in jobs_by_type.items():
        if job_type == "SE":
            stackexchange.run_jobs(conn, jobs, se_conf, tokens)

        elif job_type == "reddit":
            reddit.run_jobs(conn, jobs, tokens)

        elif job_type == "HN":
            hackernews.run_jobs(conn, jobs)

        elif job_type == "4chan":
            fourchan.run_jobs(conn, jobs)

    # cleanup database
    conn.cursor().execute("VACUUM")

    logging.info("scraping ended at {}".format(time.ctime()))


def main():
    # setup logging
    logging.basicConfig(level=logging.INFO)

    # mute noisy packages
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    se_conf = {
        "client_id": "8691",

        # app key. "This is not considered a secret, and may be
        # safely embed in client side code or distributed binaries."
        "key": "bVsLGOdziqDVuvgu974HWQ(("
    }

    tokens = {
        "se": se_load_token(),

        # get one reddit API token initially. Will auto-renew if expires (after 60 minutes)
        "reddit": reddit.get_token()
    }

    # open/create database
    conn, conn_web = init_db()

    flask_app = Flask(__name__, template_folder="static")

    def periodic_run():
        # run jobs on separate thread
        t = threading.Thread(target=run_jobs(conn, se_conf, tokens))
        t.start()

        # periodic re-calling
        seconds = 1 * 60
        threading.Timer(seconds, periodic_run).start()

    @flask_app.route('/mark_read')
    def mark_read():
        logging.info("marked as read: {}".format(list(request.args.items())))

        # set read to 1, null unnecessary info to save space
        cursor = conn_web.cursor()
        cursor.execute(
            'UPDATE posts SET read = 1, link_in = NULL, link_out = NULL, title = NULL '
            'WHERE category_id = ? AND date <= ?',
            [request.args.get("cat_id"), request.args.get("timestamp")]
        )
        conn_web.commit()
        return ""

    # Without this, the browser sometimes caches the css file. Annoying while changing things
    @flask_app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'public, max-age=0'
        response.headers['Last-Modified'] = datetime.now()
        return response

    @flask_app.route('/')
    def html_root():
        return render_template('maja.html', data=make_template_data(conn=conn_web))

    def run_flask():
        flask_app.run(port=80)

    t = threading.Thread(target=run_flask)
    t.start()

    periodic_run()


if __name__ == '__main__':
    main()
