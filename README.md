# X 自動投稿システム（ワンピース考察）

@Yama_3140 に、ワンピース考察を **AIが最新情報で生成 → 人が👍で承認 → 自動でX投稿** する仕組み。
ファーストコミュニティ集客のための取り組み。**PC非依存・追加コストほぼゼロ・規約準拠**。

---

## 全体像（セミオート承認フロー・2026-07-01〜稼働中）

```
毎朝 7:00 JST   クラウドのClaudeルーティーンがWeb検索で最新ワンピ話題を調べ、考察を生成
               → Slack #times_yama に「今日の考察案」を投稿
      │
（人）内容を見て 👍 で承認   ← ここが公開前チェック
      │
毎日 18:00 JST  GitHub Actions が 👍 を確認 → あれば本文を X に投稿 ＋ Slackに✅通知
```

**なぜ「👍承認」を挟むのか**：「無人でAIが公開SNSへ投稿」することは Claude Code / クラウドの安全機構が意図的にブロックする（AIが未確認・不適切な内容を無人で公開する事故を防ぐガードレール。回避不可＝回避すべきでない）。→ **公開前に人間が一度チェックする形が唯一かつ正しい設計**。

---

## 構成要素

| 役割 | 実体 |
|---|---|
| 生成 (朝7:00) | クラウドのルーティーン（claude.ai Code Routine, `trig_01NHjL8Cp9AJ1Pt3wBgNfBSk`, 環境「毎朝AIリサーチ用」`env_0172U11rjgVAaJavqYBwzDft`, model `claude-sonnet-4-6`）。WebSearchで最新話題→考察生成→Slackコネクタで #times_yama へ投稿。cron `0 22 * * *`(UTC)＝7:00 JST |
| 承認 | 人が #times_yama の下書きに 👍 リアクション |
| 投稿 (夕18:00) | GitHub Actions `approve-and-post.yml`（cron `0 9 * * *`＝18:00 JST）→ `approve_and_post.py` |
| 投稿先 | X @Yama_3140（無料アカウント＝1ツイート約140字/全角） |

---

## このリポジトリのファイル

- **`approve_and_post.py`** ＝【本番】Slackの👍を確認し、`===本文===`〜`===END===`の間だけ抽出。Slack記法(メンション/リンク/署名)を除去、絵文字ショートコード(`:fire:`等)→Unicode変換してから X 投稿(OAuth1)＋Slackへ✅通知。
- **`.github/workflows/approve-and-post.yml`** ＝【本番】上を毎日18:00 JSTに実行。
- `post_text.py` + `post-text.yml` ＝ 任意本文を手動でX投稿（`gh workflow run post-text.yml -f text="..."`）。テスト/手動投稿用。
- `post_queue.py` + `daily-post.yml` + `posts.json`（考察72本のプール）＝ **フォールバック（現在 disabled）**。enableすると人手なしで毎日プールから1本ずつ自動投稿（最新性は弱いが完全無人）。
- `post_latest.py` + `post-latest.yml`、`post.py` ＝ 旧方式（未使用・参考）。

---

## Secrets（GitHub → Settings → Secrets and variables → Actions）

- `X_CONSUMER_KEY` / `X_CONSUMER_SECRET` / `X_ACCESS_TOKEN` / `X_ACCESS_TOKEN_SECRET` — X OAuth1.0a 鍵（@Yama_3140、Appの権限は **Read and write**、権限変更後にトークン再生成）
- `SLACK_BOT_TOKEN` — GitHubがSlackを読む用（`xoxb-...`、scope: `channels:history`/`groups:history`/`reactions:read`/`chat:write`、Botを #times_yama に招待済み）
- `SLACK_CHANNEL_ID` — #times_yama のチャンネルID（`C...`/`G...`）
- `ANTHROPIC_API_KEY` — 現在未使用（Phase2＝GitHub上で毎回AI生成する案の名残。クレジット課金が要るため不採用）

---

## 運用方法

- **毎日やること**：朝 #times_yama に届く「考察案」を見て、良ければ **👍** を押す。それだけ。👍しなければその日は投稿されない。
- **投稿時刻を変える**：生成＝ルーティーンのcron、投稿＝`approve-and-post.yml`のcron（どちらもUTC。JST−9時間）。
- **止める**：`approve-and-post.yml` を disable、またはルーティーンを無効化（https://claude.ai/code/routines ）。
- **文面の傾向を変える**：ルーティーンのプロンプトを編集（RemoteTrigger / claude.ai）。
- **完全無人にしたい日**：`daily-post.yml`（プール）を enable（ただし👍承認は挟まらない＝最新性なし）。

## トラブルシュート

- **X投稿 401** ＝ 鍵間違い/権限（App=Read and write + トークン再生成を確認。consumer_keyに約25字のAPI Keyを入れる。Bearerトークンではない）
- **X投稿 402** ＝ X APIクレジット切れ（console.x.com「クレジット」でチャージ）
- **X投稿 403** ＝ 文字数超過（280カウント/全角約140字）or 重複投稿 or 権限
- **Slackエラー** ＝ Botのscope不足 / #times_yama未招待 / SLACK_CHANNEL_ID誤り

---

## X API / 規約メモ（2026年7月時点・**変わりやすいので使用前に要再確認**）

- **自動いいね/フォロー/引用ポスト**：2026/4/20に公式APIの自己申込ティア（pay-per-use/Basic/Pro）から削除 → **Enterprise（月$42k〜$50k）のみ**。かつ automation rules で「自動いいね」「大量・攻撃的フォロー」は明文禁止 → **永久凍結リスク**。公式API使用でも挙動ルールは適用。**やらない**。
- **自動リポスト（通常RT）**：非スパムなら明示的に許可。**DM**：未承諾の一括/自動DMは禁止（オプトインのみ）。
- **自前コンテンツの投稿**：pay-per-use課金で可。1投稿 $0.015、URL入り $0.20、サブスク/最低額なし。新規はFree廃止（2026/2/6）。
- **無料アカウント（X Premiumなし）**：1ツイート280カウント＝全角約140字（絵文字1個2, 改行1）。超過は403。長文はPremium。
- 出典：`docs.x.com/x-api/getting-started/pricing` ／ `docs.x.com/changelog`（2026-04-20の変更） ／ `help.x.com/en/rules-and-policies/x-automation`

## 将来やりたいこと（岡崎さん提案・フライホイール）

投稿URLをログ → 定期的にエンゲージ計測 → 伸びた投稿を次の生成の参考にする → 質が複利で上がる。

## やらないこと

自動いいね/フォロー/一括DM、検出回避型ブラウザ自動化は非対応（X規約違反・アカウント凍結リスク）。自前コンテンツの投稿のみ。

---
*ローカル開発用一式は `SHINSEKAI/workspace/x-auto-post/`（`post_tweet.py` + `config.json` の手元テスト、`github-repo/` がこの公開リポジトリのソース）。*
