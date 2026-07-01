# -*- coding: utf-8 -*-
"""環境変数 POST_TEXT の本文を X に投稿する。
workflow_dispatch の入力（inputs.text）を POST_TEXT に渡して使う。
Xの鍵は GitHub Secrets（環境変数）から読む。
"""
import os
import sys

import requests
from requests_oauthlib import OAuth1

TWEETS_URL = "https://api.x.com/2/tweets"
X_ENV = ("X_CONSUMER_KEY", "X_CONSUMER_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")


def main():
    missing = [k for k in X_ENV if not os.environ.get(k)]
    if missing:
        sys.exit(f"環境変数(GitHub Secrets)が未設定: {missing}")
    text = (os.environ.get("POST_TEXT") or "").strip()
    if not text:
        sys.exit("POST_TEXT が空です。")

    auth = OAuth1(os.environ["X_CONSUMER_KEY"], os.environ["X_CONSUMER_SECRET"],
                  os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_TOKEN_SECRET"])
    r = requests.post(TWEETS_URL, json={"text": text}, auth=auth, timeout=30)
    if r.status_code == 201:
        d = r.json().get("data", {})
        print(f"OK id={d.get('id')}  https://x.com/i/status/{d.get('id')}")
        print(f"    {text}")
    else:
        print(f"FAIL {r.status_code}: {r.text}")
        r.raise_for_status()


if __name__ == "__main__":
    main()
