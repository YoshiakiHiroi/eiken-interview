# QUESTIONS

実装中に出た不明点。回答をもらったら「回答」欄を埋めて残す。

| # | 日付 | 質問 | 状況 | 回答 |
|---|---|---|---|---|
| 1 | 2026-10-30 | 最新の Gemini Flash / Imagen / Chirp 3 HD が `asia-northeast1` で使えるか。使えない場合は `GCP_LOCATION` を `us-central1` などに切り替えてよいか | ブラウザでの環境構築（`docs/browser-setup-instructions.md` 手順10）で確認する | |
| 2 | 2026-10-30 | GCP プロジェクト・Firebase の作成状況（Step 2 の実機確認に必要） | プロジェクト `eiken-interview` は作成済み。残りの環境構築は `docs/browser-setup-instructions.md` で実施中。それまではモックで進める | |
| 3 | 2026-10-30 | 面接官の決まり文句に入る受験者名（仕様書の "Mr. Hiroi"）の持ち方。案: 環境変数 `CANDIDATE_NAME` を `/api/grades` の応答に差し込む | Step 2 で暫定実装済み（`CANDIDATE_NAME` を `grades/*.yaml` の `{candidate_name}` に差し込む） | |
| 4 | 2026-10-30 | Q4/Q5 で深掘り質問（"Why?" / "Why not?"）を出し分けるには、最初の回答が Yes か No かを録音直後に知る必要がある。案A: 録音後に画面の Yes/No ボタンで本人が選ぶ（確実・本番とは少し違う）。案B: 最初の録音だけを Gemini で即時判定する軽量 API を足す（本番に近いが1〜3秒待つ） | API は `yes_no` と `follow_up_audio` を受ける形で実装済み。Step 5 で決める。暫定は案A | |
