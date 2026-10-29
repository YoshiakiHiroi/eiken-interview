from datetime import UTC, datetime
from typing import Any

import pytest
from conftest import Fakes
from fastapi.testclient import TestClient

from eiken_api.models import Session

PARTS = ["read_aloud", "q1", "q2", "q3", "q4", "q5"]


def _create_session(client: TestClient, headers: dict[str, str], mode: str = "full") -> str:
    res = client.post("/api/sessions", json={"mode": mode, "set_id": "pre2_0001"}, headers=headers)
    assert res.status_code == 201
    return res.json()["session_id"]


def _submit(
    client: TestClient,
    headers: dict[str, str],
    session_id: str,
    part: str,
    audio: bytes,
    follow_up: bytes | None = None,
    yes_no: str | None = None,
) -> Any:
    data: dict[str, str] = {"duration_sec": "12.5", "silence_before_sec": "1.2", "replay_count": "1"}
    files: dict[str, tuple[str, bytes, str]] = {"audio": ("a.webm", audio, "audio/webm")}
    if yes_no:
        data["yes_no"] = yes_no
    if follow_up is not None:
        files["follow_up_audio"] = ("b.webm", follow_up, "audio/webm")
    return client.post(f"/api/sessions/{session_id}/answers/{part}", data=data, files=files, headers=headers)


def test_create_session_takes_grade_from_set(client: TestClient, fakes: Fakes, auth_headers: dict[str, str]) -> None:
    session_id = _create_session(client, auth_headers)
    session = fakes.sessions.get(session_id)
    assert session is not None
    assert (session.grade, session.uid, session.mode) == ("pre2", "u1", "full")
    missing = client.post("/api/sessions", json={"mode": "full", "set_id": "nope"}, headers=auth_headers)
    assert missing.status_code == 404


def test_submit_answer_converts_stores_and_scores(
    client: TestClient, fakes: Fakes, auth_headers: dict[str, str], audio_samples: dict[str, bytes]
) -> None:
    session_id = _create_session(client, auth_headers)
    res = _submit(client, auth_headers, session_id, "q2", audio_samples["webm"])

    assert res.status_code == 200
    body = res.json()
    assert body["score"] == 4
    assert body["issue_tags"] == ["missing_person"]
    assert body["replay_count"] == 1
    assert body["audio_url"] == f"https://signed.example/test-bucket/sessions/{session_id}/q2.wav"
    assert fakes.audio.objects[f"sessions/{session_id}/q2.wav"][:4] == b"RIFF"
    call = fakes.evaluator.calls[0]
    assert call["max"] == 5
    assert "A woman is watering flowers." in call["user"]
    assert "準2級" in call["system"]


def test_follow_up_part_sends_both_recordings(
    client: TestClient, fakes: Fakes, auth_headers: dict[str, str], audio_samples: dict[str, bytes]
) -> None:
    session_id = _create_session(client, auth_headers)
    res = _submit(client, auth_headers, session_id, "q4", audio_samples["mp4"], audio_samples["ogg"], yes_no="yes")

    assert res.status_code == 200
    assert res.json()["yes_no"] == "yes"
    assert fakes.evaluator.calls[0]["audios"] == 2
    assert "Why?" in fakes.evaluator.calls[0]["user"]
    assert f"sessions/{session_id}/q4_follow_up.wav" in fakes.audio.objects


@pytest.mark.parametrize(("part", "yes_no"), [("q4", None), ("q2", "yes")])
def test_yes_no_must_match_part(
    client: TestClient, auth_headers: dict[str, str], audio_samples: dict[str, bytes], part: str, yes_no: str | None
) -> None:
    session_id = _create_session(client, auth_headers)
    assert _submit(client, auth_headers, session_id, part, audio_samples["webm"], yes_no=yes_no).status_code == 422


def test_invalid_audio_and_unknown_part_are_rejected(
    client: TestClient, auth_headers: dict[str, str], audio_samples: dict[str, bytes]
) -> None:
    session_id = _create_session(client, auth_headers)
    assert _submit(client, auth_headers, session_id, "q1", b"garbage").status_code == 422
    assert _submit(client, auth_headers, session_id, "silent_reading", audio_samples["webm"]).status_code == 404


def test_failed_evaluation_is_saved_with_null_score(
    client: TestClient, fakes: Fakes, auth_headers: dict[str, str], audio_samples: dict[str, bytes]
) -> None:
    fakes.evaluator.fail = True
    session_id = _create_session(client, auth_headers)
    res = _submit(client, auth_headers, session_id, "q1", audio_samples["webm"])

    assert res.status_code == 200
    assert res.json()["score"] is None
    assert "broken JSON" in res.json()["evaluation_error"]
    session = fakes.sessions.get(session_id)
    assert session is not None and session.answers[0].score is None


def test_finish_full_session_scores_attitude_and_total(
    client: TestClient, fakes: Fakes, auth_headers: dict[str, str], audio_samples: dict[str, bytes]
) -> None:
    session_id = _create_session(client, auth_headers)
    for part in PARTS:
        yes_no = "no" if part in ("q4", "q5") else None
        assert _submit(client, auth_headers, session_id, part, audio_samples["webm"], yes_no=yes_no).status_code == 200
    _submit(client, auth_headers, session_id, "q1", audio_samples["webm"])

    res = client.post(f"/api/sessions/{session_id}/finish", headers=auth_headers)

    assert res.status_code == 200
    body = res.json()
    assert len(body["answers"]) == 6
    assert body["attitude"]["score"] == 3
    assert body["total"] == 4 * 6 + 3
    assert body["passed"] is True
    assert body["finished_at"] is not None


def test_reanswer_after_finish_recomputes_total(
    client: TestClient, fakes: Fakes, auth_headers: dict[str, str], audio_samples: dict[str, bytes]
) -> None:
    session_id = _create_session(client, auth_headers)
    for part in PARTS:
        _submit(
            client,
            auth_headers,
            session_id,
            part,
            audio_samples["webm"],
            yes_no="yes" if part in ("q4", "q5") else None,
        )
    client.post(f"/api/sessions/{session_id}/finish", headers=auth_headers)

    fakes.evaluator.score = 1
    _submit(client, auth_headers, session_id, "q3", audio_samples["webm"])

    session = fakes.sessions.get(session_id)
    assert session is not None
    assert session.total == 4 * 5 + 1 + 3


def test_drill_session_has_no_attitude_or_pass_judgement(
    client: TestClient, auth_headers: dict[str, str], audio_samples: dict[str, bytes]
) -> None:
    session_id = _create_session(client, auth_headers, mode="drill_q2")
    _submit(client, auth_headers, session_id, "q2", audio_samples["webm"])

    body = client.post(f"/api/sessions/{session_id}/finish", headers=auth_headers).json()

    assert body["attitude"] is None
    assert (body["total"], body["passed"]) == (4, None)


def test_other_users_session_is_hidden(client: TestClient, fakes: Fakes, auth_headers: dict[str, str]) -> None:
    fakes.sessions.save(
        Session(id="other", uid="u9", grade="pre2", mode="full", set_id="pre2_0001", started_at=datetime.now(UTC))
    )
    assert client.get("/api/sessions/other", headers=auth_headers).status_code == 404
    assert client.post("/api/sessions/other/finish", headers=auth_headers).status_code == 404
