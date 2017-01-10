import requests
import logging


def get_token():
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


def insert_to_db_reddit(conn, cursor, job, items):
    def get_link_out(data):
        if data["is_self"]:
            return None
        else:
            return data["url"]

    rows = [(
        i["data"]["id"],
        "reddit",
        job["subreddit"],
        "https://www.reddit.com{}".format(i["data"]["permalink"]),
        get_link_out(i["data"]),
        i["data"]["title"],
        i["data"]["score"],
        i["data"]["num_comments"],
        i["data"]["created"]
    ) for i in items if i["data"]["score"] >= job["score"]]

    cursor.executemany(
        'INSERT OR IGNORE INTO posts(id, category_id, link_in, link_out, title, score, comments, date)'
        'VALUES (?, (SELECT category_id from categories WHERE type = ? AND subtype = ?), ?, ?, ?, ?, ?, ?) ', rows
    )
    inserted_count = cursor.rowcount

    cursor.executemany(
        'UPDATE OR IGNORE posts SET id=?, '
        'category_id=(SELECT category_id FROM categories WHERE type = ? AND subtype = ?), '
        'link_in=?, link_out=?, title=?, score=?, comments=?, date=? '
        'WHERE read = 0', rows
    )

    conn.commit()
    return inserted_count


class ConnectionError503(ConnectionError):
    pass

class ConnectionErrorRedditAuth(ConnectionError):
    pass


def make_request(reddit_token, after, job):
    headers = {
        'user-agent': "windows:dampy:v0.1 (by /u/SE400PPp)",
        "Authorization": "bearer {}".format(reddit_token)
    }
    payload = (
        ("limit", 100),
        ("t", "week")
    )
    if after is not None:
        payload += ("after", after),

    url = 'https://oauth.reddit.com/r/{}/top'.format(job["subreddit"])
    if "keyword" in job:
        url = 'https://oauth.reddit.com/r/{}/search'.format(job["subreddit"])
        payload += ("q", job["keyword"]),
        payload += ("restrict_sr", "true"),

    r = requests.get(url, headers=headers, params=payload)
    if r.status_code == 401:
        raise ConnectionErrorRedditAuth
    elif r.status_code == 503:
        raise ConnectionError503
    r_json = r.json()
    return r_json["data"]["children"], r_json["data"]["after"]


def run_jobs(conn, cursor, jobs, reddit_token):
    inserted_rows_total = 0
    for job in jobs:
        print("  job: ", job.items())
        done = False
        after = None
        while not done:
            # Especially when searching, reddit often throws a 503 error when overloaded
            while True:
                try:
                    items, after = make_request(reddit_token, after, job)
                except ConnectionError503:
                    logging.warning("Reddit: ERROR 503. Retrying...")
                    continue
                except ConnectionErrorRedditAuth:
                    reddit_token = get_token()
                    logging.warning("Reddit: Token expired. Now token: {}. Retrying...".format(reddit_token))
                    continue
                break

            inserted_rows = insert_to_db_reddit(conn, cursor, job, items)
            inserted_rows_total += inserted_rows
            done = not (after is not None and items[-1]["data"]["score"] >= job["score"])
    logging.info("Reddit done, inserted: {}".format(inserted_rows_total))
