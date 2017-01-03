import requests

def insert_to_db_reddit(posts, conn, job, items):
    rows = [
        {
            "id": i["data"]["id"],
            "type": "reddit",
            "subtype": job["subreddit"],
            "link_in": "https://www.reddit.com{}".format(i["data"]["permalink"]),
            "link_out": i["data"]["url"],
            "score": i["data"]["score"],
            "title": i["data"]["title"],
            "comments": i["data"]["num_comments"],
            "read": 0
        } for i in items if i["data"]["score"] >= job["score"]]
    conn.execute(posts.insert().prefix_with("OR REPLACE"), rows)


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


def run_jobs(posts, conn, jobs, reddit_token):
    for job in jobs:
        print("  job: ", job.items())
        done = False
        after = None
        while not done:
            items, after = make_request(reddit_token, after, job["subreddit"])
            insert_to_db_reddit(posts, conn, job, items)
            done = not (after is not None and items[-1]["data"]["score"] >= job["score"])