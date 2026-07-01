# -*- coding: utf-8 -*-
"""GitHub Actions から毎日実行される投稿スクリプト。

- X の鍵は環境変数（GitHub Secrets）から読む（config.json は使わない）
- posts.json（考察プール）から、その日の分を1本だけ選んで投稿する
- 状態管理は不要：日付ベースで決定的に1本を選ぶ
"""
import datetime
import json
import os
import sys
from pathlib import Path

import requests
from requests_oauthlib import OAuth1

TWEETS_URL = "https://api.x.com/2/tweets"
ENV = ("X_CONSUMER_KEY", "X_CONSUMER_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")
EPOCH = datetime.date(2026, 1, 1)  # 日付インデックスの基準日


def main():
    missing = [k for k in ENV if not os.environ.get(k)]
    if missing:
        sys.exit(f"環境変数(GitHub Secrets)が未設定です: {missing}")

    posts = json.loads(Path(__file__).with_name("posts.json").read_text(encoding="utf-8"))
    if not posts:
        sys.exit("posts.json が空です。考察プールを入れてください。")

    idx = (datetime.date.today() - EPOCH).days % len(posts)
    item = posts[idx]
    text = item["text"] if isinstance(item, dict) else str(item)

    auth = OAuth1(os.environ["X_CONSUMER_KEY"], os.environ["X_CONSUMER_SECRET"],
                  os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_TOKEN_SECRET"])
    r = requests.post(TWEETS_URL, json={"text": text}, auth=auth, timeout=30)

    if r.status_code == 201:
        d = r.json().get("data", {})
        print(f"OK  idx={idx}/{len(posts)}  id={d.get('id')}  https://x.com/i/status/{d.get('id')}")
        print(f"    {text}")
    else:
        print(f"FAIL {r.status_code}: {r.text}")
        r.raise_for_status()


if __name__ == "__main__":
    main()
