import json
import webbrowser
import requests


def se_get_token(se_conf):
    base_url = "https://stackexchange.com/oauth/dialog"
    success_url = "https://stackexchange.com/oauth/login_success"
    url = "{}?client_id={}&scope=no_expiry&redirect_uri={}".format(
        base_url, se_conf["se_client_id"], success_url)
    webbrowser.open(url)


def se_load_token():
    with open('secrets.json') as data_file:
        data = json.load(data_file)
        print(data)
    return data.get("se_access_token", "")


def se_test(se_conf, se_token):
    payload = (
        ("site", "stackoverflow"),
        ("client_id", se_conf["client_id"]),
        ("key", se_conf["key"]),
        ("access_token", se_token))
    r = requests.get('https://api.stackexchange.com/2.2/questions', params=payload)
    print("url", r.url)
    print(r)
    res_json = r.json()
    backoff_time = res_json.get("backoff", -1)
    print(res_json)
    print("backoff", backoff_time)


if __name__ == '__main__':
    se_conf = {
        "client_id": "8691",

        # app key. "This is not considered a secret, and may be
        # safely embed in client side code or distributed binaries."
        "key": "bVsLGOdziqDVuvgu974HWQ(("
    }

    # se_token = se_get_token(se_conf)

    # se_test(se_conf)
