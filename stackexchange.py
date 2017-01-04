import logging
import time

import arrow
import requests


def insert_to_db(conn, cursor, items, subtype):
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
        'INSERT OR REPLACE INTO posts(id, category_id, link_in, title, score, comments)'
        'VALUES (?, (SELECT category_id from categories WHERE type = ? AND subtype = ?), ?, ?, ?, ?)', rows
    )
    conn.commit()


def make_request(se_conf, se_token, job, max_score):
    now = arrow.utcnow()
    earlier = now.replace(months=-1)

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
    if max_score is not None:
        payload += ("max", max_score),

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


def run_jobs(conn, cursor, jobs, se_conf, se_token):
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
            items, min_score, has_more, backoff, quota_remaining = make_request(se_conf, se_token, job, max_score)
            if len(items) > 0:
                insert_to_db(conn, cursor, items, subtype=job["site"])

            done = not has_more
            print("max_score:", max_score, ",  len:", len(items), ", done:", done, ", backoff:", backoff, quota_remaining)

            # same-score answers could be missing
            max_score = min_score
