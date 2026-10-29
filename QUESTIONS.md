# QUESTIONS

実装中に出た不明点。回答をもらったら「回答」欄を埋めて残す。

| # | 日付 | 質問 | 状況 | 回答 |
|---|---|---|---|---|
| 1 | 2026-10-30 | 最新の Gemini Flash / Imagen / Chirp 3 HD が `asia-northeast1` で使えるか。使えない場合は `GCP_LOCATION` を `us-central1` などに切り替えてよいか | 確認済み | Gemini: 東京は `gemini-3.5-flash` まで。最新の `gemini-3.8-flash` は `global` のみ → `GEMINI_LOCATION=global` で `gemini-3.8-flash` を使う（2026-10-30 決定）。Imagen: どちらのエンドポイントにもなし。画像生成は `global` の `gemini-nano-banana-2.1` などに置き換える必要あり（Step 4）。TTS: `en-US-Chirp3-HD-Aoede` / `Puck` とも利用可 |
| 2 | 2026-10-30 | GCP プロジェクト・Firebase の作成状況（Step 2 の実機確認に必要） | 完了 | 2026-10-30 に `docs/browser-setup-instructions.md` の手順1〜11を完了。予算は既存の「おこづかいの範囲内」（請求先の全6プロジェクト合計で月3,000円）を流用 |
| 3 | 2026-10-30 | 面接官の決まり文句に入る受験者名（仕様書の "Mr. Hiroi"）の持ち方。案: 環境変数 `CANDIDATE_NAME` を `/api/grades` の応答に差し込む | Step 2 で暫定実装済み（`CANDIDATE_NAME` を `grades/*.yaml` の `{candidate_name}` に差し込む） | |
| 4 | 2026-10-30 | Q4/Q5 で深掘り質問（"Why?" / "Why not?"）を出し分けるには、最初の回答が Yes か No かを録音直後に知る必要がある。案A: 録音後に画面の Yes/No ボタンで本人が選ぶ（確実・本番とは少し違う）。案B: 最初の録音だけを Gemini で即時判定する軽量 API を足す（本番に近いが1〜3秒待つ） | API は `yes_no` と `follow_up_audio` を受ける形で実装済み。Step 5 で決める。暫定は案A | |
