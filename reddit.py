import requests

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
    rows = [(
        i["data"]["id"],
        "reddit",
        job["subreddit"],
        "https://www.reddit.com{}".format(i["data"]["permalink"]),
        i["data"]["url"],
        i["data"]["title"],
        i["data"]["score"],
        i["data"]["num_comments"]
    ) for i in items if i["data"]["score"] >= job["score"]]

    cursor.executemany(
        'INSERT OR REPLACE INTO posts(id, type, subtype, link_in, link_out, title, score, comments)'
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?)', rows
    )
    conn.commit()


def make_request(reddit_token, after, subreddit):
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

    r = requests.get('https://oauth.reddit.com/r/{}/top'.format(subreddit),
                     headers=headers,
                     params=payload)
    r_json = r.json()
    return r_json["data"]["children"], r_json["data"]["after"]


def run_jobs(conn, cursor, jobs, reddit_token):
    for job in jobs:
        print("  job: ", job.items())
        done = False
        after = None
        while not done:
            items, after = make_request(reddit_token, after, job["subreddit"])
            insert_to_db_reddit(conn, cursor, job, items)
            done = not (after is not None and items[-1]["data"]["score"] >= job["score"])