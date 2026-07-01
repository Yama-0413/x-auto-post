# -*- coding: utf-8 -*-
"""posts.json（考察プール）から未投稿の先頭を1件だけ投稿し、posted:true を書き戻す。
GitHub Actions から毎日実行。Xの鍵は環境変数(GitHub Secrets)から読む。
状態(posted)はワークフローがコミットして次回に引き継ぐ→重複しない順送り。
"""
import json
import os
import sys
from pathlib import Path

import requests
from requests_oauthlib import OAuth1

TWEETS_URL = "https://api.x.com/2/tweets"
X_ENV = ("X_CONSUMER_KEY", "X_CONSUMER_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")
QUEUE = Path(__file__).with_name("posts.json")


def main():
    missing = [k for k in X_ENV if not os.environ.get(k)]
    if missing:
        sys.exit(f"環境変数(GitHub Secrets)が未設定: {missing}")

    posts = json.loads(QUEUE.read_text(encoding="utf-8"))
    nxt = next((p for p in posts if not p.get("posted")), None)
    if not nxt:
        print("キューが空です（全て投稿済み）。posts.json を補充してください。")
        return

    auth = OAuth1(os.environ["X_CONSUMER_KEY"], os.environ["X_CONSUMER_SECRET"],
                  os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_TOKEN_SECRET"])
    r = requests.post(TWEETS_URL, json={"text": nxt["text"]}, auth=auth, timeout=30)

    if r.status_code == 201:
        d = r.json().get("data", {})
        print(f"OK id={d.get('id')}  https://x.com/i/status/{d.get('id')}")
        print(f"    {nxt['text'][:60]}")
        nxt["posted"] = True
        nxt["tweet_id"] = d.get("id")
        QUEUE.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
        remaining = sum(1 for p in posts if not p.get("posted"))
        print(f"残りキュー: {remaining} 件")
    else:
        print(f"FAIL {r.status_code}: {r.text}")
        r.raise_for_status()


if __name__ == "__main__":
    main()
