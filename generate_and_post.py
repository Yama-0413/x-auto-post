# -*- coding: utf-8 -*-
"""GitHub Actions から毎日実行：AIが考察を1本生成 → Xに投稿。

- ANTHROPIC_API_KEY（GitHub Secret）で Claude を呼び、考察を生成
- X の鍵4つ（GitHub Secrets）で OAuth 1.0a 投稿
毎回テーマをランダムに選び、日付を添えて新規に生成する（重複しにくくする）。
"""
import datetime
import os
import sys

import anthropic
import requests
from requests_oauthlib import OAuth1

TWEETS_URL = "https://api.x.com/2/tweets"
X_ENV = ("X_CONSUMER_KEY", "X_CONSUMER_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")

MODEL = "claude-opus-4-8"  # 安くするなら "claude-haiku-4-5"
MAX_CHARS = 1200  # 安全上限（暴走防止）。Xの長文は Premium 加入が前提

# Claude に Web 検索をさせて最新情報を拾う（server tool・opus-4-8対応）
TOOLS = [{"type": "web_search_20260209", "name": "web_search"}]

SYSTEM = """あなたはワンピース考察が得意なSNS運用者。X(旧Twitter)向けに、今まさに話題の最新トピックを踏まえた考察ポストを1本つくる。
手順とルール:
- まず web 検索で直近の情報（最新話・公式発表・ファンの間で盛り上がっている話題）を確認する。
- 日本語。長文可（読み応えのある数百字の考察にしてよいが、冗長にはしない）。
- 考察=推測。断定して誤情報にしない。過度なネタバレ断定は避けつつ、話題性のある切り口にする。
- 多くのファンが「わかる」「気になる」と反応したくなる内容とフックにする。URLは貼らない。ハッシュタグは0〜1個。
- 炎上・誹謗中傷・不健全な内容は禁止。
- 出力は投稿本文のみ。検索の説明・「調べます」等の前置き・思考・引用符は一切書かない。"""


def generate():
    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY を自動で読む
    today = datetime.date.today().isoformat()
    messages = [{
        "role": "user",
        "content": f"いまワンピース界隈で盛り上がっている最新トピックを1つ選び、それについての考察ポストを本文だけ作ってください。今日は {today}。",
    }]
    msg = None
    for _ in range(6):  # web検索でpause_turnになったら継続
        msg = client.messages.create(
            model=MODEL, max_tokens=2000, system=SYSTEM, tools=TOOLS, messages=messages,
        )
        if msg.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": msg.content})
            continue
        break
    # テキストブロックのうち最後の非空＝最終的な投稿本文
    texts = [b.text for b in msg.content if b.type == "text" and b.text.strip()]
    text = (texts[-1] if texts else "").strip().strip('「」"\'').strip()
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS - 1] + "…"
    return text, "web検索ベース"


def post(text):
    auth = OAuth1(os.environ["X_CONSUMER_KEY"], os.environ["X_CONSUMER_SECRET"],
                  os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_TOKEN_SECRET"])
    r = requests.post(TWEETS_URL, json={"text": text}, auth=auth, timeout=30)
    if r.status_code == 201:
        d = r.json().get("data", {})
        print(f"OK id={d.get('id')}  https://x.com/i/status/{d.get('id')}")
    else:
        print(f"FAIL {r.status_code}: {r.text}")
        r.raise_for_status()


def main():
    missing = [k for k in X_ENV if not os.environ.get(k)]
    if missing:
        sys.exit(f"環境変数(GitHub Secrets)が未設定: {missing}")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY が未設定です（GitHub Secrets に登録してください）。")
    text, theme = generate()
    print(f"[生成] テーマ={theme}\n{text}\n")
    post(text)


if __name__ == "__main__":
    main()
