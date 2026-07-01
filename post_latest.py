# -*- coding: utf-8 -*-
"""latest.txt の内容を X に投稿する。
クラウドのルーティーンが latest.txt を更新して push すると、
GitHub Actions がこれを実行して投稿する（クラウドは投稿しない）。
Xの鍵は環境変数(GitHub Secrets)から読む。
"""
import os
import sys
from pathlib import Path

import requests
from requests_oauthlib import OAuth1

TWEETS_URL = "https://api.x.com/2/tweets"
X_ENV = ("X_CONSUMER_KEY", "X_CONSUMER_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")
LATEST = Path(__file__).with_name("latest.txt")


def main():
    missing = [k for k in X_ENV if not os.environ.get(k)]
    if missing:
        sys.exit(f"環境変数(GitHub Secrets)が未設定: {missing}")
    if not LATEST.exists():
        sys.exit("latest.txt がありません。")
    text = LATEST.read_text(encoding="utf-8").strip()
    if not text:
        sys.exit("latest.txt が空です。")

    auth = OAuth1(os.environ["X_CONSUMER_KEY"], os.environ["X_CONSUMER_SECRET"],
                  os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_TOKEN_SECRET"])
    r = requests.post(TWEETS_URL, json={"text": text}, auth=auth, timeout=30)
    if r.status_code == 201:
        d = r.json().get("data", {})
        print(f"OK id={d.get('id')}  https://x.com/i/status/{d.get('id')}")
        print(f"    {text[:60]}")
    else:
        print(f"FAIL {r.status_code}: {r.text}")
        r.raise_for_status()


if __name__ == "__main__":
    main()
