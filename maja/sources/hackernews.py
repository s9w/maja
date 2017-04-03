import arrow
import logging
import requests
import html
import common


def get_tags(job):
    tags = "story"
    if job.get("self") == "ask":
        tags += ",ask_hn"
    elif job.get("self") == "show":
        tags += ",show_hn"
    elif job.get("self") == "both":
        tags += ",(ask_hn,show_hn)"
    return tags


def make_request(job, page=0):
    now = arrow.utcnow()
    earlier = now.replace(weeks=-1)
    api_url = "https://hn.algolia.com/api/v1/search"
    payload = (
        ("tags", (get_tags(job))),
        ("numericFilters", "points>={},created_at_i>{}".format(job["score"], earlier.timestamp)),
        ("hitsPerPage", 100),
        ("page", page)
    )

    if "keyword" in job:
        payload += ("query", job["keyword"]),

    r = requests.get(api_url, params=payload)
    res_json = r.json()

    return res_json["hits"], res_json["nbPages"]


def get_row(item):
    return (
        item["objectID"],
        "HN",
        "",
        "https://news.ycombinator.com/item?id={}".format(item["objectID"]),
        item["url"],
        html.unescape(item["title"]),
        item["points"],
        item["num_comments"],
        item["created_at_i"]
    )


def get_rows(items):
    return [get_row(item) for item in items]


def run_jobs(conn, cursor, jobs):
    inserted_rows_total = 0
    for job in jobs:
        done = False
        page = 0
        while not done:
            items, pages = make_request(job, page)
            if len(items) > 0:
                rows = get_rows(items)
                inserted_rows = common.insert_to_db(conn, cursor, rows)
                inserted_rows_total += inserted_rows

            if pages > page + 1:
                done = False
                page += 1
            else:
                done = True
    logging.info("HN done, inserted: {}".format(inserted_rows_total))
