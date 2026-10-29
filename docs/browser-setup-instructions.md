# GCP / Firebase 環境構築 指示書（Claude in Chrome 向け）

あなたはブラウザ上で Google Cloud コンソールと Firebase コンソールを操作し、英検面接練習アプリ「eiken-interview」の実行環境を整える。下の「作業ルール」を守り、「作業手順」を上から順に進め、最後に「報告フォーマット」で結果を返すこと。

## 前提

| 項目 | 値 |
|---|---|
| GCP プロジェクト ID | `eiken-interview`（作成済み） |
| GCP プロジェクト番号 | `210054687174` |
| 操作するアカウント | `yoshiaki.hiroi@gmail.com`（プロジェクトのオーナー） |
| リージョン | `asia-northeast1`（東京）。大阪（asia-northeast2）は使わない |
| 用途 | 1ユーザー専用の個人アプリ。公開運用はしない |

## 作業ルール

1. **ログイン・パスワード・2段階認証の入力はしない。** 求められたら作業を止め、ユーザーに操作を依頼する。
2. **請求先アカウントの作成・変更はしない。** 未設定なら作業を止めて報告する。
3. **サービスアカウントの鍵（JSON キー）は作らない。** 画面で勧められても作らない。
4. **バケットやデータを公開しない。** `allUsers` / `allAuthenticatedUsers` への権限付与は禁止。
5. **ここに書かれていないリソースは作らない・消さない。** 既に同じ名前のリソースがある場合は、作り直さず設定値を確認して報告する。
6. 手順どおりにいかない場合（ボタンが見つからない、エラーが出るなど）は、推測で別の設定を選ばず、画面の文言をそのまま記録して次の手順へ進む。
7. 各手順が終わるたびに、結果（成功 / 既存 / 失敗と理由）を記録しておく。

## 作業手順

### 1. 請求先の確認

1. Google Cloud コンソールでプロジェクト `eiken-interview` を選ぶ。
2. 「お支払い」を開き、請求先アカウントがリンクされているか確認する。
3. リンクされていなければ、ここで作業を止めて報告する（以降の手順は請求先が必要）。

### 2. API の有効化

「API とサービス」→「ライブラリ」で次を検索し、それぞれ「有効にする」。有効済みならそのままでよい。

- Cloud Run Admin API
- Artifact Registry API
- Cloud Build API
- Cloud Firestore API
- Cloud Storage（Google Cloud Storage JSON API）
- Vertex AI API
- Cloud Text-to-Speech API
- Identity Toolkit API
- IAM Service Account Credentials API（署名付き URL の発行に必要）

### 3. Firebase の追加

1. Firebase コンソール（https://console.firebase.google.com/）を開く。
2. 「プロジェクトを追加」→「既存の Google Cloud プロジェクトに Firebase を追加」で `eiken-interview` を選ぶ。
3. Google アナリティクスは **無効** にする。
4. 料金プランの確認が出た場合は、プロジェクトに紐づいている請求先のまま進める（プランの変更はしない）。

### 4. Firebase Authentication（Google ログイン）

1. Firebase コンソール →「Authentication」→「始める」。
2. 「Sign-in method」で **Google** を有効にする。プロジェクトのサポートメールは `yoshiaki.hiroi@gmail.com` を選ぶ。
3. 「Settings」→「承認済みドメイン」に次があることを確認する（無ければ追加）。
   - `localhost`
   - `eiken-interview.web.app`
   - `eiken-interview.firebaseapp.com`

### 5. Web アプリの登録

1. Firebase コンソール →「プロジェクトの設定」→「マイアプリ」→ Web アプリ（`</>`）を追加する。
2. アプリのニックネームは `eiken-interview-web`。
3. 「Firebase Hosting も設定する」に **チェックを入れる**（サイトは既定の `eiken-interview`）。
4. 表示された `firebaseConfig` の各値（`apiKey`, `authDomain`, `projectId`, `storageBucket`, `messagingSenderId`, `appId`）を記録する。SDK のインストール手順や CLI の手順は実行しなくてよい。

### 6. Firestore データベース

1. Google Cloud コンソール →「Firestore」→「データベースを作成」。
2. データベース ID: `(default)`、モード: **ネイティブモード**、ロケーション: **asia-northeast1（東京）** の単一リージョン。
3. セキュリティルールは **本番環境モード（すべて拒否）** を選ぶ。アプリはサーバ経由でのみアクセスするため、クライアント向けの許可は不要。
4. 作成後、「インデックス」→「複合」で次のインデックスを作成する。
   - コレクション ID: `sets`、クエリのスコープ: コレクション
   - フィールド: `grade` 昇順 → `enabled` 昇順 → `usage_count` 昇順

### 7. Cloud Storage バケット

「Cloud Storage」→「バケットを作成」で次の設定にする。

| 項目 | 値 |
|---|---|
| 名前 | `eiken-interview-assets`（使えない場合は `eiken-interview-assets-210054687174`） |
| ロケーションタイプ | Region、`asia-northeast1` |
| ストレージクラス | Standard |
| 公開アクセスの防止 | **有効** |
| アクセス制御 | **均一** |
| 保護（バージョニング・保持ポリシー） | 設定しない |

### 8. Artifact Registry リポジトリ

「Artifact Registry」→「リポジトリを作成」。

| 項目 | 値 |
|---|---|
| 名前 | `eiken-api` |
| 形式 | Docker |
| モード | 標準 |
| ロケーション | Region、`asia-northeast1` |

### 9. サービスアカウントと権限

1. 「IAM と管理」→「サービスアカウント」→「作成」。
   - 名前 / ID: `eiken-api-sa`
   - 説明: `Cloud Run runtime for eiken-api`
2. 「IAM」画面で、プロジェクトに対して `eiken-api-sa@eiken-interview.iam.gserviceaccount.com` に次のロールを付ける。
   - Cloud Datastore ユーザー（`roles/datastore.user`）
   - Vertex AI ユーザー（`roles/aiplatform.user`）
3. バケット `eiken-interview-assets` の「権限」タブで、同じサービスアカウントに次のロールを付ける（プロジェクト全体ではなくバケットに付ける）。
   - Storage オブジェクト管理者（`roles/storage.objectAdmin`）
4. サービスアカウント `eiken-api-sa` 自身の「権限」タブで、同じサービスアカウントに次のロールを付ける（署名付き URL を鍵なしで発行するため）。
   - サービス アカウント トークン作成者（`roles/iam.serviceAccountTokenCreator`）

### 10. Vertex AI / TTS が東京リージョンで使えるかの確認（変更なし・確認のみ）

1. Vertex AI の Model Garden（または「Vertex AI Studio」）で、`asia-northeast1` を選んだ状態で次が使えるか確認し、使えるモデル名（例 `gemini-2.5-flash`）を記録する。
   - Gemini の Flash 系の最新モデル
   - Imagen の最新モデル
2. Cloud Text-to-Speech のドキュメントまたはコンソールで、`en-US-Chirp3-HD-Aoede` と `en-US-Chirp3-HD-Puck` が使えるか確認する。使えなければ、使える `en-US` の Neural2 音声（男性・女性1つずつ）の名前を記録する。
3. ここではモデルの有効化や課金を伴う操作はしない。

### 11. 予算アラート（任意だが推奨）

「お支払い」→「予算とアラート」で、プロジェクト `eiken-interview` に対して月額 **3,000 円** の予算を作り、50% / 90% / 100% で `yoshiaki.hiroi@gmail.com` にメール通知する設定にする。既に予算がある場合は作らずに報告する。

## 報告フォーマット

作業が終わったら、次の形式で結果を返すこと。

```markdown
## 結果

| # | 手順 | 結果 | 備考 |
|---|---|---|---|
| 1 | 請求先の確認 | 成功 / 既存 / 失敗 | |
| 2 | API の有効化 | | 有効化できなかった API があれば列挙 |
| 3 | Firebase の追加 | | |
| 4 | Authentication | | |
| 5 | Web アプリの登録 | | |
| 6 | Firestore + インデックス | | |
| 7 | バケット | | 実際のバケット名 |
| 8 | Artifact Registry | | |
| 9 | サービスアカウントと権限 | | 付与したロール |
| 10 | モデル確認 | | |
| 11 | 予算アラート | | |

## 記録した値

- firebaseConfig: apiKey= / authDomain= / projectId= / storageBucket= / messagingSenderId= / appId=
- バケット名:
- Gemini モデル名（asia-northeast1 で利用可）:
- Imagen モデル名（asia-northeast1 で利用可）:
- TTS 音声名（男性 / 女性）:

## 判断を保留したこと・エラー

- （画面の文言をそのまま）
```
