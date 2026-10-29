# eiken-interview

英検 二次試験（面接）を本番形式で練習するための個人用 Web アプリ。仕様は [`docs/eiken-interview-dev-spec.md`](docs/eiken-interview-dev-spec.md) を参照。

## 構成

| ディレクトリ | 内容 |
|---|---|
| `api/` | FastAPI（Python 3.12, uv）。Cloud Run にデプロイする |
| `web/` | Vite + React 18 + TypeScript + Tailwind。Firebase Hosting に配信する |
| `scripts/` | 問題セットの生成・レビュー用スクリプト |

## 前提ツール

- uv、Python 3.12
- Node.js 22、npm
- ffmpeg（API のローカル実行時に必要）
- gcloud CLI、firebase CLI（デプロイ時）
- pre-commit

## セットアップ

```bash
make install
pre-commit install
```

## 開発コマンド

| コマンド | 内容 |
|---|---|
| `make lint` | ruff（api）と ESLint + Prettier（web） |
| `make typecheck` | pyright（api）と tsc（web） |
| `make test` | pytest（api）と vitest（web） |
| `make format` | 自動整形 |
| `make api-dev` | API を `http://localhost:8080` で起動 |
| `make web-dev` | Web を `http://localhost:5173` で起動 |

## API の環境変数

`api/.env.example` を `api/.env` にコピーして値を埋める。必須値が欠けていると API は起動時にエラーで止まる。

| 変数 | 内容 |
|---|---|
| `DEFAULT_GRADE` | 既定の級（`api/eiken_api/grades/{grade}.yaml` が存在すること） |
| `GCP_PROJECT` / `GCP_LOCATION` | GCP プロジェクト ID / リージョン |
| `ASSETS_BUCKET` | 問題素材・録音を置く GCS バケット |
| `ALLOWED_EMAILS` | ログインを許可するメール（カンマ区切り） |
| `CORS_ORIGINS` | 許可するオリジン（カンマ区切り） |
| `SIGNED_URL_TTL_SEC` | 署名付き URL の有効秒数 |
| `CANDIDATE_NAME` | 面接官が呼ぶ受験者名（例 `Mr. Hiroi`） |

## 動作確認

```bash
gcloud auth application-default login
make api-dev
curl http://localhost:8080/healthz   # {"status":"ok"}
```

### Firestore のダミーセットで `/api/sets` を確認する（Step 2）

```bash
# 複合インデックス（grade, enabled, usage_count）を作成
gcloud firestore indexes composite create --project=<project> \
  --collection-group=sets --query-scope=COLLECTION \
  --field-config=field-path=grade,order=ascending \
  --field-config=field-path=enabled,order=ascending \
  --field-config=field-path=usage_count,order=ascending

# ダミーセットを登録
cd api && uv run python ../scripts/seed_dummy_set.py --project <project> --grade pre2

# Firebase ID トークンを取得して呼び出す（トークンは Web ログイン後に取得）
curl -H "Authorization: Bearer $ID_TOKEN" "http://localhost:8080/api/grades"
curl -H "Authorization: Bearer $ID_TOKEN" "http://localhost:8080/api/sets/next?grade=pre2"
```

## GCP の準備とデプロイ

Step 7 で記載する。
