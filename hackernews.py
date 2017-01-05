import arrow
import requests

def make_request(job, page=0):
    now = arrow.utcnow()
    earlier = now.replace(weeks=-1)
    api_url = "https://hn.algolia.com/api/v1/search"
    payload = (
        ("tags", "story"),
        ("numericFilters", "points>={},created_at_i>{}".format(job["score"], earlier.timestamp)),
        ("hitsPerPage", 100),
        ("page", page)
    )
    r = requests.get(api_url, params=payload)
    res_json = r.json()

    return res_json["hits"], res_json["nbPages"]


def insert_to_db(conn, cursor, items):
    rows = []
    for item in items:
        rows.append((
            item["objectID"],
            "HN",
            "",
            "https://news.ycombinator.com/item?id={}".format(item["objectID"]),
            item["url"],
            item["title"],
            item["points"],
            item["num_comments"],
            item["created_at_i"]
        ))

    cursor.executemany(
        'INSERT OR REPLACE INTO posts(id, category_id, link_in, link_out, title, score, comments, date)'
        'VALUES (?, (SELECT category_id from categories WHERE type = ? AND subtype = ?), ?, ?, ?, ?, ?, ?)', rows
    )
    conn.commit()


def run_jobs(conn, cursor, jobs):
    for job in jobs:
        done = False
        page = 0
        while not done:
            items, pages = make_request(job, page)
            if len(items) > 0:
                insert_to_db(conn, cursor, items)

            if pages > page + 1:
                done = False
                page += 1
            else:
                done = True