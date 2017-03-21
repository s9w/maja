import html

import arrow
import logging
import requests
import time

def get_text(thread):
    string = html.unescape("{} {}".format(thread.get("sub", ""), thread.get("com", "")))
    if len(string) > 100:
        return "{}...".format(string[:100])
    return string

def make_request(job, page=0):
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
           get_text(thread), \
           0, \
           thread.get("replies", 0), \
           thread["time"]

def insert_to_db(conn, cursor, job, items):
    def criteria(thread):
        comment_criteria = thread.get("replies", 0) >= job.get("comments", 0)
        if "keyword" in job:
            keyword_criteria = get_text(thread).find(job["keyword"]) != -1
        else:
            keyword_criteria = True
        return comment_criteria and keyword_criteria

    rows = [get_row(thread, job["board"]) for page in items for thread in page["threads"] if criteria(thread)]

    # print("rowcount", cursor.rowcount)
    cursor.executemany(
        'INSERT OR IGNORE INTO posts(id, category_id, link_in, link_out, title, score, comments, date)'
        'VALUES (?, (SELECT category_id from categories WHERE type = ? AND subtype = ?), ?, ?, ?, ?, ?, ?) ', rows
    )
    inserted_count = cursor.rowcount

    cursor.executemany(
        'UPDATE OR IGNORE posts SET id=?, '
        'category_id=(SELECT category_id from categories WHERE type = ? AND subtype = ?), '
        'link_in=?, link_out=?, title=?, score=?, comments=?, date=? '
        'WHERE read = 0', rows
    )
    conn.commit()

    return inserted_count


def run_jobs(conn, cursor, jobs):
    inserted_rows_total = 0
    for job in jobs:
        items = make_request(job)
        inserted_rows = insert_to_db(conn, cursor, job, items)
        inserted_rows_total += inserted_rows

        time.sleep(1) # 4chan API demands max 1 request per second
    logging.info("4chan done, inserted: {}".format(inserted_rows_total))