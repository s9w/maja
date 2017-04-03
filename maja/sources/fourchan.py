import html

import arrow
import logging
import requests
import time
import common


def get_thread_title(thread, shorten=100):
    """generates a string representation of/from a thread"""
    title = html.unescape("{} {}".format(thread.get("sub", ""), thread.get("com", "")))
    if shorten and len(title) > shorten:
        return "{}...".format(title[:100])
    return title


def make_request(job):
    now = arrow.utcnow()
    earlier = now.replace(weeks=-1)
    api_url = "http://a.4cdn.org/{}/catalog.json".format(job["board"])
    payload = (
        ("If-Modified-Since", str(earlier.timestamp)),
    )

    r = requests.get(api_url, params=payload)
    return r.json()


def get_row(thread, board):
    return thread["no"], \
           "4chan", \
           board, \
           "http://boards.4chan.org/{}/thread/{}".format(board, thread["no"]), \
           None, \
           get_thread_title(thread), \
           0, \
           thread.get("replies", 0), \
           thread["time"]


def get_rows(items, job):
    def criteria(thread):
        comment_criteria = thread.get("replies", 0) >= job.get("comments", 0)
        if "keyword" in job:
            keyword_criteria = get_thread_title(thread, shorten=False).find(job["keyword"]) != -1
        else:
            keyword_criteria = True
        return all([comment_criteria, keyword_criteria])

    rows = [get_row(thread, job["board"]) for page in items for thread in page["threads"] if criteria(thread)]
    return rows


def run_jobs(conn, cursor, jobs):
    inserted_rows_total = 0
    for job in jobs:
        items = make_request(job)
        rows = get_rows(items, job)
        inserted_rows = common.insert_to_db(conn, cursor, rows)
        inserted_rows_total += inserted_rows

        time.sleep(1) # 4chan API demands max 1 request per second
    logging.info("4chan done, inserted: {}".format(inserted_rows_total))