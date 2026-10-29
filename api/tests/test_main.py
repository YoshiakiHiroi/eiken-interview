import pytest
from conftest import OUTSIDER_TOKEN, fake_signer, fake_verifier, make_settings
from fastapi.testclient import TestClient

from eiken_api.main import create_app


def test_healthz(client: TestClient) -> None:
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_unknown_default_grade_fails_at_startup() -> None:
    with pytest.raises(ValueError, match="DEFAULT_GRADE"):
        create_app(
            settings=make_settings(default_grade="pre9"),
            token_verifier=fake_verifier,
            set_repository=None,  # pyright: ignore[reportArgumentType]
            url_signer=fake_signer,
        )


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({}, 401),
        ({"Authorization": "Bearer broken"}, 401),
        ({"Authorization": f"Bearer {OUTSIDER_TOKEN}"}, 403),
    ],
)
def test_api_requires_allowed_user(client: TestClient, headers: dict[str, str], expected: int) -> None:
    assert client.get("/api/grades", headers=headers).status_code == expected
    assert client.get("/api/sets/next?grade=pre2", headers=headers).status_code == expected


def test_list_grades(client: TestClient, auth_headers: dict[str, str]) -> None:
    res = client.get("/api/grades", headers=auth_headers)
    assert res.status_code == 200
    [pre2] = res.json()
    assert pre2["grade"] == "pre2"
    assert pre2["max_score_total"] == 33
    assert pre2["phrases"]["turn_over"] == "Now, Mr. Test, please turn over the card and put it down."


def test_next_set_returns_least_used_enabled_set_with_signed_urls(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    res = client.get("/api/sets/next?grade=pre2&mode=full", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == "pre2_0002"
    assert body["passage"]["audio_model_url"] == "https://signed.example/test-bucket/sets/pre2_0002/passage_model.mp3"
    assert body["questions"][0]["audio_url"].startswith("https://signed.example/")
    assert body["common_audio"]["greeting"].startswith("https://signed.example/")


def test_next_set_filters_by_grade(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get("/api/sets/next?grade=pre9", headers=auth_headers).status_code == 404


def test_next_set_rejects_unknown_mode(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get("/api/sets/next?grade=pre2&mode=bogus", headers=auth_headers).status_code == 422


def test_get_set(client: TestClient, auth_headers: dict[str, str]) -> None:
    res = client.get("/api/sets/pre2_0001", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == "pre2_0001"
    assert client.get("/api/sets/missing", headers=auth_headers).status_code == 404
