# -*- coding: utf-8 -*-
"""GitHub Actions から毎日実行：AIが考察を1本生成 → Xに投稿。

- ANTHROPIC_API_KEY（GitHub Secret）で Claude を呼び、考察を生成
- X の鍵4つ（GitHub Secrets）で OAuth 1.0a 投稿
毎回テーマをランダムに選び、日付を添えて新規に生成する（重複しにくくする）。
"""
import datetime
import os
import random
import sys

import anthropic
import requests
from requests_oauthlib import OAuth1

TWEETS_URL = "https://api.x.com/2/tweets"
X_ENV = ("X_CONSUMER_KEY", "X_CONSUMER_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")

MODEL = "claude-opus-4-8"  # 安くするなら "claude-haiku-4-5"

THEMES = [
    "空白の100年とDの意志",
    "ラフテルとひとつなぎの大秘宝の正体",
    "古代兵器（プルトン/ポセイドン/ウラヌス）",
    "ジョイボーイと太陽の神ニカ",
    "世界政府・五老星・イム様の目的",
    "悪魔の実の起源と本質",
    "レッドライン/月/失われた王国など世界の謎",
    "主要キャラの出自・名前の伏線と回収予想",
]

SYSTEM = """あなたはワンピース考察が得意なSNS運用者。X(旧Twitter)に投稿する考察ツイートを1本だけ作る。
ルール:
- 日本語、130字以内。URL禁止、ハッシュタグは0〜1個。
- 考察=推測なので「〜説」「〜では？」など断定を避けた語り口。事実を断定して誤情報にしない。
- 最新話の具体的なネタバレには踏み込まず、広く知られた設定・謎・伏線をベースにする。
- 読者が反応したくなる問いかけやフックを入れる。炎上・不健全な内容は禁止。
- 出力は投稿本文のみ。前置き・説明・思考・引用符・「以下が〜」などは一切書かない。"""


def generate():
    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY を自動で読む
    theme = random.choice(THEMES)
    today = datetime.date.today().isoformat()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": f"テーマ「{theme}」で、{today} 用の新しい考察ツイートを1本、本文だけ出力してください。",
        }],
    )
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    # 念のため前後のクオートを除去し、長すぎたら切り詰める
    text = text.strip('「」"\'' ).strip()
    if len(text) > 140:
        text = text[:139] + "…"
    return text, theme


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
