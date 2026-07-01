# -*- coding: utf-8 -*-
"""Slack #times_yama の「今日の考察案」に 👍 が付いていれば、その本文を X に投稿する。
18:00 JST に GitHub Actions から実行。承認(👍)が無ければ何もしない。

必要な環境変数(GitHub Secrets):
  SLACK_BOT_TOKEN     : xoxb-... （scope: channels:history or groups:history, reactions:read, chat:write）
  SLACK_CHANNEL_ID    : #times_yama のチャンネルID（C... / G...）
  X_CONSUMER_KEY 等4つ : Xの OAuth1 鍵
"""
import os
import sys
import time

import requests
from requests_oauthlib import OAuth1

TWEETS_URL = "https://api.x.com/2/tweets"
X_ENV = ("X_CONSUMER_KEY", "X_CONSUMER_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")
MARKER = "===本文==="          # ルーティーンがこの後ろに考察本文を置く
OK_REACTIONS = {"+1", "thumbsup"}  # 👍


def slack(method, params, post=False):
    url = f"https://slack.com/api/{method}"
    headers = {"Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}"}
    if post:
        headers["Content-Type"] = "application/json; charset=utf-8"
        r = requests.post(url, headers=headers, json=params, timeout=30)
    else:
        r = requests.get(url, headers=headers, params=params, timeout=30)
    d = r.json()
    if not d.get("ok"):
        sys.exit(f"Slack API {method} エラー: {d.get('error')}")
    return d


def notify(channel, text, thread_ts=None):
    body = {"channel": channel, "text": text}
    if thread_ts:
        body["thread_ts"] = thread_ts
    try:
        slack("chat.postMessage", body, post=True)
    except SystemExit:
        pass  # 通知失敗は致命的でない


def main():
    missing = [k for k in X_ENV if not os.environ.get(k)]
    if missing:
        sys.exit(f"X の鍵が未設定: {missing}")
    for k in ("SLACK_BOT_TOKEN", "SLACK_CHANNEL_ID"):
        if not os.environ.get(k):
            sys.exit(f"{k} が未設定です。")
    channel = os.environ["SLACK_CHANNEL_ID"]

    hist = slack("conversations.history", {"channel": channel, "limit": 30})
    now = time.time()
    draft = None
    for m in hist.get("messages", []):  # 新しい順
        if MARKER in m.get("text", "") and (now - float(m["ts"])) < 20 * 3600:
            draft = m
            break
    if not draft:
        print("今日の『考察案』が見つかりません（朝のルーティーン未投稿 or 古い）。何もしません。")
        return

    approved = any(rx.get("name") in OK_REACTIONS for rx in draft.get("reactions", []))
    if not approved:
        print("👍が付いていないので投稿しません。")
        notify(channel, "🕕 18時になりましたが 👍 が無かったので、今日の考察は投稿しませんでした。", draft["ts"])
        return

    text = draft["text"].split(MARKER, 1)[1].strip()
    if not text:
        sys.exit("本文が空です。")

    auth = OAuth1(os.environ["X_CONSUMER_KEY"], os.environ["X_CONSUMER_SECRET"],
                  os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_TOKEN_SECRET"])
    r = requests.post(TWEETS_URL, json={"text": text}, auth=auth, timeout=30)
    if r.status_code == 201:
        d = r.json().get("data", {})
        url = f"https://x.com/i/status/{d.get('id')}"
        print(f"OK 投稿: {url}")
        notify(channel, f"✅ Xに投稿しました！\n{url}", draft["ts"])
    else:
        print(f"FAIL {r.status_code}: {r.text}")
        notify(channel, f"⚠️ X投稿に失敗 {r.status_code}: {r.text[:200]}", draft["ts"])
        r.raise_for_status()


if __name__ == "__main__":
    main()
