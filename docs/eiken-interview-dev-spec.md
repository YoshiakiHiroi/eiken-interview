# 英検 二次試験（面接）対策サイト 開発指示書

- 初期対象級: **準2級**（将来 2級以上を追加する前提で、級を設定データとして扱う。「2-1. 級の拡張性」参照）
- 作成日: 2026-10-30
- 発注者: 廣井（個人利用）
- 実装担当: Claude Code（ローカル）
- 受験予定: 2026年11月中（第2回 二次試験）
- 利用者: 発注者本人のみ（1ユーザー・短期集中利用）

---

## 0. この文書の読み方

本書は Claude Code に開発を依頼するための仕様書である。**「12. 実装順序」の順に進め、各ステップの完了条件を満たしてから次へ進むこと。** 不明点は推測で進めず、`QUESTIONS.md` に書き出して作業を止めずに次のタスクへ進む（判断が必要な箇所は後述の「13. 判断ルール」を優先する）。

GCP プロジェクト・GitHub リポジトリは発注者が事前に作成する。Claude Code はそれらが存在する前提で作業する（名称は「1. 名称」参照）。

---

## 1. 名称

| 対象 | 名称 | 備考 |
|---|---|---|
| GitHub リポジトリ | `eiken-interview` | 個人アカウント配下。private |
| GCP プロジェクト ID | `eiken-interview` | 重複で取れない場合は `eiken-interview-hiroi` |
| GCP リージョン | `asia-northeast1`（東京） | Vertex AI の Gemini / Imagen が揃うため。Osaka ではなく東京で統一 |
| Cloud Run サービス | `eiken-api` | バックエンド API |
| Firebase Hosting サイト | `eiken-interview`（既定） | `https://eiken-interview.web.app` |
| Cloud Storage バケット | `eiken-interview-assets` | 問題イラスト・TTS 音声・回答録音 |
| Firestore データベース | `(default)` / Native mode / `asia-northeast1` | |
| Artifact Registry | `eiken-api`（Docker） | `asia-northeast1-docker.pkg.dev/<project>/eiken-api/api` |
| サービスアカウント | `eiken-api-sa@<project>.iam.gserviceaccount.com` | Cloud Run 実行用 |
| npm パッケージ名（web） | `eiken-interview-web` | |
| Python パッケージ名（api） | `eiken_api` | |

---

## 2. 目的とスコープ

英検準2級二次試験（個人面接）を本番形式で繰り返し練習し、AI 面接官による採点・講評・模範解答で弱点を潰すための **自分専用 Web アプリ** を作る。

### スコープ内
- 本番形式の通し模擬面接（音声入出力、タイマー付き）
- パート別ドリル（音読 / Q2 イラスト描写 / Q3 状況説明 / Q4・Q5 意見）
- AI 採点（英検の配点に準拠）、文字起こし、講評、模範解答
- 履歴・弱点集計
- 定型表現カード
- 問題セットの事前生成スクリプト（Gemini + Imagen）

### スコープ外
- 複数ユーザー対応、課金、公開運用、SEO
- リアルタイム対話（Gemini Live API）— ターン制で十分
- 音素レベルの発音スコアリング（Gemini の所見ベースで足りる）
- 一次試験（筆記・リスニング）対策
- 2級以上の問題セット・プロンプトの実装（**ただし追加できる構造にしておくこと**。下記 2-1）

### 2-1. 級の拡張性（必須の設計要件）

初期実装は準2級のみだが、今後 2級（さらに準1級）を追加する。**コード・名称・データのどこにも「準2級専用」であることを埋め込まない**。

- 級は識別子 `grade` で扱う: `pre2` / `2` / `pre1`（文字列）。URL・Firestore・GCS パス・環境変数・プロンプトファイル名に `pre2` をハードコードせず、`grade` 変数から組み立てる
- **級ごとの試験構成は設定ファイルで定義する**: `api/eiken_api/grades/{grade}.yaml`（またはフロントと共有する JSON）。定義する内容は、パートの並びと種類（`silent_reading`, `read_aloud`, `passage_question`, `picture_actions`, `picture_situation`, `picture_story`, `opinion`, `personal` など）、各パートの配点、黙読秒数、準備時間の有無（2級 Q2 の「20秒考える時間」など）、面接官の決まり文句、合格目安点。フロントの通しフローはこの定義を読んで画面遷移・タイマーを組み立てる（準2級固有の順序を if 文で書かない）
- 採点プロンプトは **パートの種類単位** で持つ（`prompts/{part_type}.md`）。級による差分（語数、求める文数、語彙レベル）はプロンプトに `grade` と級設定から渡す変数で注入する。級ごとに完全に別の観点が必要なパート（2級の3コマイラストのナレーション等）は新しい `part_type` として追加する
- Firestore の `sets` に `grade` フィールドを持たせ、`GET /api/sets/next?grade=pre2` のように級で絞る。`sessions` にも `grade` を保存する
- 問題生成スクリプトは `--grade pre2` を引数に取り、級設定と級別の生成プロンプト（`prompts/generate_set_{grade}.md`）を使う
- フロントの Home で級を選べる UI（初期は準2級のみ表示でよいが、選択状態を `grade` として全画面に引き回す）
- 履歴・集計は級で絞り込めるようにする
- 定型表現カードは `phrases.json` を級ごとのキーで持つ

---

## 3. 試験形式（実装の正 — 準2級 `grade=pre2`）

準2級二次試験は約6分の個人面接で、次の流れ・配点に固定されている。アプリはこれを忠実に再現する。**この表の内容を `grades/pre2.yaml` に落とし込むこと**（2級追加時は `grades/2.yaml` を足すだけで通しフローが動く構造にする）。

| # | パート | 内容 | 配点 |
|---|---|---|---|
| 0 | 黙読 | パッセージ（約50語）を **20秒** 黙読 | - |
| 1 | 音読 | パッセージを音読（時間制限なし、目安30〜40秒） | 5 |
| Q1 | パッセージ質問 | パッセージの内容についての質問。"How / Why ..." 型。本文の "so / by doing so / in this way" 等の前後を使って答える | 5 |
| Q2 | イラストA 描写 | 5人の人物がそれぞれ別の動作をしている絵。**全員の動作を現在進行形で** 描写 | 5 |
| Q3 | イラストB 状況説明 | 1人（または2人）の状況説明。「〜したいが〜できない（because ...）」型 | 5 |
| Q4 | 意見 | "Do you think ...?" → Yes/No → "Why? / Why not?" → 理由を2文程度 | 5 |
| Q5 | 自分のこと | "Do you ...?" → Yes/No → 深掘り質問（"Please tell me more." / "Why not?"）→ 2文程度 | 5 |
| - | アティチュード | 積極性・明瞭さ・反応の速さ | 3 |
| | **合計** | | **33** |

- 合格目安: 19点前後（アプリ内では 19 点を合格ラインとして表示する）
- 面接官の決まり文句も再現する: 入室時の挨拶（"Hello." / "May I have your card, please?" / "My name is ... May I have your name, please?" / "This is the Grade Pre-2 test, OK?"）、黙読指示（"First, please read the passage silently for twenty seconds."）、音読指示（"Now, please read it aloud."）、質問前（"Now, I'm going to ask you five questions."）、イラストを見せる指示（"Please look at the picture and describe the situation."）、カード返却（"Now, Mr. Hiroi, please turn over the card and put it down."）、終了（"This is the end of the test. May I have your card back, please? ... You may go now. Goodbye."）

---

## 4. 機能要件

### 4.1 模擬面接（通し）モード
1. 開始ボタン → 未使用（または最も使用回数の少ない）問題セットを1件取得
2. 面接官音声（事前生成 TTS）で挨拶 → 問題カード（パッセージ＋イラストA/B）を画面表示
3. 黙読 20秒カウントダウン（本番同様、画面にはパッセージのみ）
4. 音読: 録音開始 → ユーザーが「回答終了」ボタン → 録音停止
5. Q1〜Q5: 各質問を TTS 再生 → 自動で録音開始 → 「回答終了」で停止。Q4/Q5 は Yes/No 回答後に深掘り質問（"Why?" 等）を再生し、再度録音（2段階）
6. 全回答をサーバへ送信 → 採点結果画面（項目別スコア、合計/33、合格ライン判定、各回答の文字起こし・講評・模範解答、アティチュード所見）
7. 各質問について「もう一度答える」で再録音・再採点できる

補助機能:
- 質問の **再生し直し** ボタン（本番でも1回は聞き返せる。"Could you say that again?" を練習できるよう、聞き返し回数を記録してアティチュード講評に反映）
- 「回答時間」を各回答で計測し、無言時間が長い場合は講評で指摘
- 画面はモバイルファースト（通勤中にスマホで使う）

### 4.2 パート別ドリルモード
- 音読ドリル: パッセージだけを連続で出題。発音・区切り・イントネーションの所見
- Q2 ドリル: イラストAだけを連続出題。言えた動作/抜けた動作を明示
- Q3 ドリル: イラストBだけを連続出題
- Q4/Q5 ドリル: 意見質問だけを連続出題。Yes/No + 理由2文の構成チェック
- 各ドリルは「10問連続」「終了まで」を選べる。採点は各回答ごとに即時表示

### 4.3 復習・集計
- セッション一覧（日時、モード、合計点、合格判定）
- セッション詳細（4.1 の結果画面と同じ）
- 集計: 項目別平均点の推移（折れ線）、直近10セッションの合計点推移、**繰り返し指摘された文法・表現ミスの頻出ランキング**（LLM が返す `issue_tags` を集計: 例 `missing_be_verb`, `third_person_s`, `no_reason_given`, `only_one_sentence`, `wrong_tense`, `mispronunciation:<word>`）
- 録音音声の再生

### 4.4 定型表現カード
- パート別の定型表現を静的 JSON で持ち、面接前に一覧できる画面
- 例: 音読（"/" で区切る位置の考え方）、Q1（"By doing so, they can ..." / "Because ..."）、Q2（"A man is carrying a box." "Two girls are talking."）、Q3（"She wants to ..., but she can't because ..."）、Q4/Q5（"Yes, I do. I think ... because ..." / "No, I don't. ... For example, ..."）、聞き返し（"I beg your pardon?" / "Could you say that again, please?"）
- 内容は `web/src/data/phrases.json` に実装側で初期データを用意してよい（発注者が後で編集する）

### 4.5 問題セット生成（オフラインスクリプト）
- `scripts/generate_sets.py --grade pre2` で問題セットを Gemini に JSON 生成させ、Imagen でイラストを生成し、TTS で質問音声を事前生成して GCS + Firestore に登録する
- 初回は **30セット** 生成する。トピックは過去問傾向に合わせる（環境、健康、テクノロジー、買い物、旅行、学校、仕事、食、ボランティア、ペット等）
- 生成後、`scripts/review_sets.py`（または簡易 HTML）で発注者がセットを一覧・無効化できるようにする（`enabled: false`）

---

## 5. 技術構成

```
[ブラウザ: React SPA]  -- Firebase Hosting (HTTPS)
   |  Firebase Auth (Google ログイン) で ID トークン取得
   |  MediaRecorder で録音 (audio/webm;codecs=opus)
   v
[Cloud Run: eiken-api (FastAPI, Python 3.12)]
   |-- Firebase Admin で ID トークン検証 + メールアドレス許可リスト
   |-- ffmpeg で webm → 16kHz mono WAV に変換
   |-- Vertex AI Gemini (音声を直接入力) → 文字起こし + 採点 + 講評 JSON
   |-- Firestore: sets / sessions
   |-- Cloud Storage: 録音・イラスト・TTS 音声 (署名付き URL で配信)
   
[オフライン: scripts/]
   |-- Gemini: 問題セット JSON 生成
   |-- Imagen: イラスト生成
   |-- Cloud Text-to-Speech: 面接官音声の事前生成
```

### 採用技術
- フロント: Vite + React 18 + TypeScript、React Router、状態管理は軽量（Zustand 可）、UI は Tailwind CSS。グラフは Recharts
- バックエンド: Python 3.12 + FastAPI + uvicorn。SDK は `google-genai`（`vertexai=True`）、`google-cloud-firestore`、`google-cloud-storage`、`google-cloud-texttospeech`、`firebase-admin`。コンテナに `ffmpeg` を同梱
- モデル: Gemini は **利用可能な最新の Flash 系**（2.5 Flash 以降）。モデル名は環境変数 `GEMINI_MODEL` で差し替え可能にする。Imagen も利用可能な最新を環境変数 `IMAGEN_MODEL` で指定
- TTS: `en-US` のネイティブ音声（Chirp 3 HD または Neural2。男性・女性を1つずつ用意し、セットごとにランダムに割り当て）。話速 0.95
- 認証: Firebase Auth（Google プロバイダ）。API 側で `ALLOWED_EMAILS` 環境変数のメールのみ許可
- IaC は不要。デプロイは `Makefile` + `gcloud` コマンドで行う（発注者が実行）
- CI: GitHub Actions で lint / typecheck / test のみ（デプロイは手動）

---

## 6. リポジトリ構成

```
eiken-interview/
├── README.md                 # セットアップ・デプロイ手順（発注者が実行する gcloud コマンドを全て記載）
├── QUESTIONS.md              # 実装中の不明点
├── Makefile                  # build / deploy / generate-sets など
├── .github/workflows/ci.yml
├── firebase.json / .firebaserc
├── api/
│   ├── Dockerfile            # python:3.12-slim + ffmpeg
│   ├── pyproject.toml        # uv または pip。ruff + mypy + pytest
│   ├── eiken_api/
│   │   ├── main.py           # FastAPI app, CORS, auth dependency
│   │   ├── auth.py           # Firebase ID token 検証 + allowlist
│   │   ├── routers/ sets.py, sessions.py, evaluate.py, phrases.py
│   │   ├── services/ gemini.py, tts.py, storage.py, firestore.py, audio.py
│   │   ├── grades/ pre2.yaml            # 級ごとの試験構成（パート並び・配点・秒数・決まり文句・合格目安）
│   │   ├── prompts/ evaluate_read_aloud.md, evaluate_passage_question.md, evaluate_picture_actions.md, evaluate_picture_situation.md, evaluate_opinion_personal.md, evaluate_attitude.md, generate_set_pre2.md
│   │   └── models.py         # Pydantic スキーマ（API と Firestore 共通）
│   └── tests/
├── web/
│   ├── package.json  (eiken-interview-web)
│   ├── src/
│   │   ├── pages/ Home, Interview, Drill, History, SessionDetail, Stats, Phrases
│   │   ├── components/ Recorder, Timer, QuestionPlayer, ScoreCard, PictureCard
│   │   ├── lib/ api.ts, auth.ts, audio.ts
│   │   └── data/ phrases.json
│   └── ...
└── scripts/
    ├── generate_sets.py      # 問題セット生成（Gemini + Imagen + TTS → GCS + Firestore）
    ├── review_sets.py        # セット一覧・有効/無効切替
    └── seed_phrases.py
```

---

## 7. データモデル（Firestore）

### `sets/{setId}`
```jsonc
{
  "id": "pre2_0001",
  "grade": "pre2",
  "enabled": true,
  "topic": "Recycling",
  "voice": "en-US-Chirp3-HD-Aoede",         // このセットの面接官音声
  "passage": {
    "title": "Recycling at Home",
    "text": "Many people today ... By doing so, they can ...", // 約50語
    "key_sentence": "By doing so, ...",       // Q1 の根拠となる文
    "audio_model_url": "gs://.../sets/pre2_0001/passage_model.mp3" // 模範音読（TTS）
  },
  "questions": [
    { "no": 1, "type": "passage", "text": "According to the passage, how can people ...?",
      "model_answer": "By ..., they can ...", "audio_url": "gs://.../q1.mp3" },
    { "no": 2, "type": "picture_a", "text": "Now, please look at the picture and describe the situation.",
      "picture_url": "gs://.../picture_a.png",
      "actions": ["A man is carrying a box.", "A woman is watering flowers.", "...5件"],
      "audio_url": "gs://.../q2.mp3" },
    { "no": 3, "type": "picture_b", "text": "Now, look at the woman in Picture B. Please describe the situation.",
      "picture_url": "gs://.../picture_b.png",
      "model_answer": "She wants to open the door, but she can't because her hands are full.",
      "audio_url": "gs://.../q3.mp3" },
    { "no": 4, "type": "opinion", "text": "Do you think more people will ... in the future?",
      "follow_up_yes": "Why?", "follow_up_no": "Why not?",
      "model_answer_yes": "...", "model_answer_no": "...", "audio_url": "...", "follow_up_audio_yes_url": "...", "follow_up_audio_no_url": "..." },
    { "no": 5, "type": "personal", "text": "Do you often ...?",
      "follow_up_yes": "Please tell me more.", "follow_up_no": "Why not?",
      "model_answer_yes": "...", "model_answer_no": "...", "audio_url": "...", "follow_up_audio_yes_url": "...", "follow_up_audio_no_url": "..." }
  ],
  "common_audio": { "greeting": "gs://...", "silent_reading": "gs://...", "read_aloud": "gs://...", "five_questions": "gs://...", "turn_over": "gs://...", "end": "gs://..." },
  "usage_count": 0,
  "created_at": "<timestamp>"
}
```
- `common_audio` は音声（voice）ごとに1回だけ生成し、`voices/{voice}/common/*.mp3` に置いて参照する（セットごとに作らない）

### `sessions/{sessionId}`
```jsonc
{
  "id": "...", "uid": "...", "grade": "pre2", "mode": "full" | "drill_read" | "drill_q2" | "drill_q3" | "drill_q45",
  "set_id": "pre2_0001", "started_at": "...", "finished_at": "...",
  "answers": [
    { "part": "read_aloud" | "q1" | "q2" | "q3" | "q4" | "q5",
      "audio_url": "gs://.../sessions/<id>/q2.wav",
      "duration_sec": 18.2, "silence_before_sec": 1.4, "replay_count": 0,
      "transcript": "...", "score": 4,
      "feedback_ja": "...", "model_answer": "...", "issue_tags": ["missing_be_verb"] }
  ],
  "attitude": { "score": 3, "feedback_ja": "..." },
  "total": 27, "passed": true
}
```

---

## 8. API 仕様（Cloud Run / FastAPI）

全エンドポイントは `Authorization: Bearer <Firebase ID token>` 必須。

| Method | Path | 説明 |
|---|---|---|
| GET | `/api/grades` | 利用可能な級と各級の試験構成（`grades/*.yaml` の内容）を返す。フロントはこれでフローを組み立てる |
| GET | `/api/sets/next?grade=pre2&mode=full` | 指定した級の有効セットのうち `usage_count` 最小を1件返す（GCS の URL は署名付き URL に変換して返す） |
| GET | `/api/sets/{id}` | セット取得 |
| POST | `/api/sessions` | セッション作成 `{mode, set_id}` → `{session_id}` |
| POST | `/api/sessions/{id}/answers/{part}` | `multipart/form-data`: `audio`(webm), `duration_sec`, `silence_before_sec`, `replay_count`, `yes_no`(q4/q5のみ)。サーバで WAV 変換 → GCS 保存 → Gemini 採点 → 回答を保存して採点結果を返す |
| POST | `/api/sessions/{id}/finish` | アティチュード採点（全回答のメタ情報＋文字起こしから）と合計計算 → セッション確定 |
| GET | `/api/sessions?grade=pre2&limit=50` | 一覧（`grade` 省略時は全級） |
| GET | `/api/sessions/{id}` | 詳細（音声は署名付き URL） |
| GET | `/api/stats?grade=pre2` | 集計（項目別平均推移、issue_tags 頻度） |
| GET | `/api/phrases?grade=pre2` | 定型表現（静的 JSON をそのまま返す。フロントに同梱でも可） |

- 採点は回答ごとに行う（通し面接でも各回答送信時に採点し、結果画面は保存済みデータを表示する）。これにより再録音・再採点が単純になる
- Gemini の応答は **JSON スキーマ強制**（`response_mime_type="application/json"` + `response_schema`）で受け取る
- タイムアウト: Cloud Run は 120 秒。Gemini 呼び出しは 60 秒でリトライ1回
- エラー時はフロントで再送できるよう、録音データはブラウザ側にも保持する

---

## 9. 採点プロンプト要件（`api/eiken_api/prompts/*.md`）

共通:
- システム指示: 「あなたは英検準2級二次試験の面接委員。英検の採点基準に従い厳格かつ一貫して採点する。フィードバックは日本語、模範解答は英語」
- 入力: 音声（WAV）＋ パート固有のコンテキスト（パッセージ本文、正解の動作リスト、質問文、Yes/No 等）
- 出力 JSON: `transcript`（聞こえた通りの英語。不明瞭な部分は `[unclear]`）、`score`（0〜5 整数）、`feedback_ja`（3〜5文。良かった点1つ＋改善点）、`model_answer`（英語、準2級レベルの語彙で）、`issue_tags`（下記の固定語彙から）、`confidence`（0〜1）
- `issue_tags` 固定語彙: `missing_be_verb`, `wrong_tense`, `third_person_s`, `article_error`, `plural_error`, `no_reason_given`, `only_one_sentence`, `off_topic`, `too_short`, `long_silence`, `japanese_used`, `unclear_pronunciation`, `mispronunciation:<word>`, `missing_person`（Q2 で人物を言い落とした）, `not_progressive`（Q2 で進行形でない）, `no_because`（Q3/Q4/Q5）, `yes_no_mismatch`（Yes/No と理由が矛盾）

パート別の観点:
- 音読: 発音の明瞭さ、意味の区切り（チャンク）、イントネーション、速さ（速すぎ/遅すぎ）、読み飛ばし・読み違い。`transcript` と本文の差分（読めなかった語）を `mispronunciation:<word>` で返す。5=ほぼ完璧、3=意味は伝わるが複数の誤り、1=多数の誤りで伝わりにくい
- Q1: 質問に対応する本文箇所を使えているか。主語を代名詞に置き換えているか（"they" 等）。本文の丸読み（質問に答えていない）は減点
- Q2: 5人全員について進行形で描写できたか。`actions` と照合して言えた/言えていない動作を `feedback_ja` に列挙。4人=4点、3人=3点を目安
- Q3: 「〜したいが〜できない」＋理由の構造。because の有無
- Q4/Q5: Yes/No の明示 → 理由が2文以上あるか → 理由が質問と論理的につながるか。1文のみは最大3点
- アティチュード（`finish` 時）: 各回答の `silence_before_sec`、`duration_sec`、`replay_count`、`transcript` の「声の大きさ・はっきりさ」所見（各回答の評価で `clarity` を補助的に返させておく）から 0〜3 を決める。ルールベース＋LLM 所見の併用で構わない

---

## 10. 問題セット生成の要件（`scripts/generate_sets.py`）

1. `generate_set_{grade}.md` プロンプトで Gemini にセット JSON を生成させる。制約:
   - パッセージは 45〜55 語、3文構成、2文目または3文目に "so / by doing so / in this way / because of this" のいずれかを含む（Q1 の根拠）
   - Q1 は "How / Why / What ..." で、答えがパッセージの該当文から作れること
   - イラストAは「屋内または屋外の1場面で5人がそれぞれ明確に異なる日常動作をしている」ことをテキストで定義し、`actions` に進行形の5文を出す
   - イラストBは「1人が何かをしたいができない状況」をテキストで定義し、`model_answer` を出す
   - Q4 は "Do you think ...?" 型、Q5 は "Do you ...? / Have you ever ...?" 型で受験者本人についての質問
   - 過去問の **転載はしない**（オリジナル生成）
2. Imagen でイラスト生成。プロンプト方針: "simple flat line illustration, black outline, light colors, clear and uncluttered, no text" ＋ 場面と5人の動作を番号付きで記述。**5人を1枚に描き分けられない場合に備え**、`--picture-mode=split` オプションで人物ごとに1枚ずつ生成して横並び合成する（Pillow）フォールバックを実装する。既定は `single` で生成し、`review_sets.py` で発注者が見て差し替える運用
3. TTS: セット内の全質問・深掘り質問・模範音読を生成。`common_audio` は voice ごとに1回
4. 生成物は `gs://eiken-interview-assets/sets/{setId}/`（`setId` に級が含まれる） に置き、Firestore `sets` に登録
5. 冪等: 同じ `setId` は上書きせずスキップ。`--grade pre2 --count 30 --start 1` のように級と件数を指定。`setId` は `{grade}_{連番4桁}`
6. 1セット生成ごとにログ出力。失敗したセットはスキップして続行し、最後にサマリを表示

---

## 11. 画面仕様（フロント）

- `/` Home: 「模擬面接を始める」「ドリル」「履歴」「集計」「表現カード」、直近の合計点と合格ライン
- `/interview`: 4.1 の通しフロー。画面上部に「現在のパート」「タイマー」、中央に問題カード（黙読中はパッセージのみ、Q2/Q3 中は該当イラストのみ大きく表示、Q4/Q5 中はカード非表示＝本番と同じ）、下部に「録音中」インジケータと「回答終了」ボタン、「もう一度質問を聞く」ボタン
- `/interview/result/:sessionId`: 合計点（/33）と合格判定を大きく、項目別スコア表、各パートのアコーディオン（自分の録音再生、文字起こし、講評、模範解答、「もう一度答える」）
- `/drill/:kind`: 1問ずつ出題→録音→即時採点→次へ
- `/history`, `/history/:id`, `/stats`（Recharts）、`/phrases`
- ログイン画面（Google）。未許可メールは「アクセス権がありません」を表示
- マイク権限未許可・非対応ブラウザのエラー表示
- iOS Safari で MediaRecorder の MIME が `audio/mp4` になる場合に対応する（サーバは webm / mp4 / ogg いずれも ffmpeg で受ける）

---

## 12. 実装順序と完了条件

各ステップの完了時に `git commit`（Conventional Commits）。ステップ内で動作確認コマンドを README に追記する。

| Step | 内容 | 完了条件 |
|---|---|---|
| 1 | リポジトリ雛形、`api`/`web`/`scripts` の初期化、lint/typecheck/test の CI、README 骨子 | `make lint test` がローカルで通る。CI が green |
| 2 | `api`: 認証、Firestore/GCS クライアント、`models.py`、`grades/pre2.yaml` と `/api/grades`、`/api/sets/*` | ローカル（`gcloud auth application-default login`）で Firestore に手投入したダミーセットが取得できる |
| 3 | `api`: 音声変換（ffmpeg）＋ Gemini 採点サービス＋ `/answers/{part}`。プロンプト6種 | `tests/fixtures/*.wav`（Claude Code が TTS で作ったサンプル回答でよい）を cURL で投げ、スキーマ通りの JSON が返る。採点のユニットテストはモック |
| 4 | `scripts/generate_sets.py` + `review_sets.py` | `--count 3` で3セットが GCS/Firestore に登録され、イラスト・音声が再生できる |
| 5 | `web`: 認証、Home、通し面接フロー、結果画面 | ローカル `vite dev` から Cloud Run（またはローカル api）に接続し、通しで1セッション完走できる |
| 6 | `web`: ドリル、履歴、集計、表現カード | 各画面が動作 |
| 7 | Dockerfile、`Makefile deploy`、Firebase Hosting 設定、README の発注者向け手順（API 有効化、SA 作成と IAM、バケット作成、Firestore 作成、Firebase Auth 設定、環境変数、デプロイ） | README の手順だけで発注者がデプロイできる |
| 8 | 仕上げ: モバイル表示、エラーハンドリング、再送、`usage_count` 更新、30セット生成 | 発注者がスマホで通し面接を完走できる |

Step 3 と 4 は Step 2 完了後に並行可。Step 5 は Step 3 の API が動いていればダミーセットで開始してよい。

---

## 13. 判断ルール（迷ったとき）

- 本番の試験形式に忠実であること > 機能の多さ
- 級固有の値（秒数・配点・決まり文句・パート順）はコードに書かず `grades/{grade}.yaml` に置く。「準2級だから」という分岐を書きそうになったら設定に逃がす
- 受験日までの時間が最優先。凝った UI より動く通しフロー
- モデル名・リージョン・バケット名などは **必ず環境変数/設定ファイル** に出し、コードに埋めない
- Gemini の出力が JSON として壊れた場合は1回リトライ、それでも駄目なら `score: null` で保存してフロントに「採点失敗・再採点」ボタンを出す
- 1ユーザー前提なので、Firestore のセキュリティルールは「API 経由のみ」（クライアントから直接 Firestore を触らない）
- 外部ライブラリは必要最小限。認証・録音・グラフ以外は標準機能で
- 英検の過去問・公式教材の文章・イラストは使用しない（すべて生成オリジナル）

---

## 14. 環境変数（api）

| 変数 | 例 |
|---|---|
| `DEFAULT_GRADE` | `pre2` |
| `GCP_PROJECT` | `eiken-interview` |
| `GCP_LOCATION` | `asia-northeast1` |
| `GEMINI_MODEL` | 利用可能な最新 Flash（例: `gemini-2.5-flash`） |
| `IMAGEN_MODEL` | 利用可能な最新 Imagen |
| `TTS_VOICES` | `en-US-Chirp3-HD-Aoede,en-US-Chirp3-HD-Puck`（男女1つずつ。利用不可なら Neural2 に置換） |
| `ASSETS_BUCKET` | `eiken-interview-assets` |
| `ALLOWED_EMAILS` | 発注者のメール（カンマ区切り） |
| `CORS_ORIGINS` | `https://eiken-interview.web.app,http://localhost:5173` |
| `SIGNED_URL_TTL_SEC` | `3600` |

---

## 15. 非機能・コスト

- Cloud Run: min instances 0、max 2、CPU 1 / 1GiB、同時実行 10
- 想定コスト: 1日3セッション × 6回答の Gemini Flash 音声入力 + TTS 事前生成分で月数百円以内
- ログ: 構造化ログ（JSON）で `session_id` / `part` / `latency_ms` を出す
- 個人情報: 録音は本人のみ。GCS バケットは非公開、署名付き URL のみで配信

---

## 16. 発注者が事前に行う作業（Claude Code は手順を README に書き起こすこと）

1. GitHub に `eiken-interview`（private）を作成
2. GCP プロジェクト `eiken-interview` を作成、請求先を紐づけ
3. 有効化する API: Cloud Run, Artifact Registry, Cloud Build（不要なら省略可）, Firestore, Cloud Storage, Vertex AI, Cloud Text-to-Speech, Identity Toolkit（Firebase Auth）
4. Firebase プロジェクトとして登録し、Hosting と Auth（Google）を有効化
5. 上記以外（SA 作成、IAM、バケット、Firestore DB 作成、デプロイ）は README の `gcloud` コマンドを順に実行する
