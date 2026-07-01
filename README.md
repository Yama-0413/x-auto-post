# X 自動投稿（GitHub Actions版）

ワンピース考察を **毎日自動でXに投稿** する。GitHubのクラウド上で動くので **PCを閉じていても投稿される**。

## 仕組み
- GitHub Actions が毎日 21:00 JST に `post.py` を実行
- `posts.json`（考察ネタのプール）から、その日の分を1本選んで投稿
- Xの鍵は GitHub の **Secrets** に保存（コードには書かない）

## 必要な Secrets（Settings → Secrets and variables → Actions）
| 名前 | 中身 |
|---|---|
| `X_CONSUMER_KEY` | API Key（コンシューマーキー・約25文字） |
| `X_CONSUMER_SECRET` | API Key Secret |
| `X_ACCESS_TOKEN` | アクセストークン |
| `X_ACCESS_TOKEN_SECRET` | アクセストークンシークレット |

## テスト実行
GitHubの **Actions タブ → Daily X Post → Run workflow** で手動実行できる。

## 投稿時刻を変える
`.github/workflows/daily-post.yml` の `cron` を編集。
例）朝8時JST = `0 23 * * *`（UTCで前日23時）。1日2回にするなら行を増やす。

## ネタを追加する
`posts.json` に `{"text": "考察本文", "theme": "テーマ"}` を追記するだけ。

## やらないこと
自動いいね/フォロー/DMは非対応（X規約違反・凍結リスクのため）。自分のオリジナル投稿の自動化のみ。
