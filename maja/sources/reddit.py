import requests
import logging
import html
import common


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
    r = requests.post(endpoint, data=post_data, headers=headers, auth=(client_id, ""))

    token = r.json()["access_token"]
    return token


def get_row(item_data, subreddit):
    def get_link_out(data):
        if data["is_self"]:
            return None
        else:
            return data["url"]

    return item_data["id"], \
           "reddit", \
           subreddit, \
           "https://www.reddit.com{}".format(item_data["permalink"]), \
           get_link_out(item_data), \
           html.unescape(item_data["title"]), \
           item_data["score"], \
           item_data["num_comments"], \
           item_data["created"]


def get_rows(items, job):
    def criteria(item_data):
        score_criteria = item_data["score"] >= job["score"]

        if "self" in job:
            self_criteria = item_data["is_self"] == job.get("self")
        else:
            self_criteria = True
        return all([score_criteria, self_criteria])

    rows = [get_row(i["data"], job["subreddit"]) for i in items if criteria(i["data"])]
    return rows


class ConnectionError503(ConnectionError):
    pass


class ConnectionErrorRedditAuth(ConnectionError):
    pass


def make_request(reddit_token, after, job):
    def get_payload():
        payload = (
            ("limit", 100),
            ("t", "week")
        )

        if after is not None:
            payload += ("after", after),

        if "keyword" in job:
            payload += ("q", job["keyword"]),
            payload += ("restrict_sr", "true"),

        return payload

    def get_url():
        if "keyword" in job:
            url = 'https://oauth.reddit.com/r/{}/search'
        else:
            url = 'https://oauth.reddit.com/r/{}/top'
        return url.format(job["subreddit"])

    headers = {
        'user-agent': "windows:dampy:v0.1 (by /u/SE400PPp)",
        "Authorization": "bearer {}".format(reddit_token)
    }

    r = requests.get(get_url(), headers=headers, params=get_payload())
    if r.status_code == 401:  # Unauthorized
        raise ConnectionErrorRedditAuth
    elif r.status_code == 503:  # Service unavailable
        raise ConnectionError503
    r_json = r.json()
    return r_json["data"]["children"], r_json["data"]["after"]


def run_jobs(conn, cursor, jobs, tokens):
    inserted_rows_total = 0
    for job in jobs:
        done = False
        after = None
        while not done:
            # Especially when searching, reddit often throws a 503 error when overloaded
            while True:
                try:
                    items, after = make_request(tokens["reddit"], after, job)
                except ConnectionError503:
                    logging.warning("Reddit: ERROR 503. Retrying...")
                    continue
                except ConnectionErrorRedditAuth:
                    tokens["reddit"] = get_token()
                    logging.warning("Reddit: Token expired. Now token: {}. Retrying...".format(tokens["reddit"]))
                    continue
                break

            rows = get_rows(items, job)
            inserted_rows = common.insert_to_db(conn, cursor, rows)
            inserted_rows_total += inserted_rows
            done = not (after is not None and items[-1]["data"]["score"] >= job["score"])
    logging.info("{} Reddit jobs done, inserted: {}".format(len(jobs), inserted_rows_total))
