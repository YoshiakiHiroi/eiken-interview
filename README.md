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

## 動作確認

```bash
make api-dev
curl http://localhost:8080/healthz   # {"status":"ok"}
```

## GCP の準備とデプロイ

Step 7 で記載する。
