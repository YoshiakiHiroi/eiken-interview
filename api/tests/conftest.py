from collections.abc import Mapping
from typing import Any

import pytest
from fastapi.testclient import TestClient

from eiken_api.config import Settings
from eiken_api.main import create_app
from eiken_api.models import ProblemSet

ALLOWED_EMAIL = "owner@example.com"
VALID_TOKEN = "valid-token"
OUTSIDER_TOKEN = "outsider-token"


def make_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "default_grade": "pre2",
        "gcp_project": "test-project",
        "gcp_location": "asia-northeast1",
        "assets_bucket": "test-bucket",
        "allowed_emails": ALLOWED_EMAIL,
        "cors_origins": "http://localhost:5173",
        "signed_url_ttl_sec": 3600,
        "candidate_name": "Mr. Test",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)  # pyright: ignore[reportCallIssue]


def fake_verifier(token: str) -> Mapping[str, Any]:
    tokens = {
        VALID_TOKEN: {"uid": "u1", "email": ALLOWED_EMAIL, "email_verified": True},
        OUTSIDER_TOKEN: {"uid": "u2", "email": "someone@example.com", "email_verified": True},
    }
    if token not in tokens:
        raise ValueError("bad token")
    return tokens[token]


def fake_signer(url: str) -> str:
    return url.replace("gs://", "https://signed.example/")


def make_set(set_id: str, grade: str = "pre2", usage_count: int = 0, enabled: bool = True) -> ProblemSet:
    return ProblemSet.model_validate(
        {
            "id": set_id,
            "grade": grade,
            "enabled": enabled,
            "topic": "Recycling",
            "voice": "en-US-Chirp3-HD-Aoede",
            "passage": {
                "title": "Recycling at Home",
                "text": "Many people today recycle. By doing so, they can reduce waste.",
                "key_sentence": "By doing so, they can reduce waste.",
                "audio_model_url": f"gs://test-bucket/sets/{set_id}/passage_model.mp3",
            },
            "questions": [
                {
                    "no": 1,
                    "type": "passage",
                    "text": "According to the passage, how can people reduce waste?",
                    "audio_url": f"gs://test-bucket/sets/{set_id}/q1.mp3",
                }
            ],
            "common_audio": {"greeting": "gs://test-bucket/voices/aoede/common/greeting.mp3"},
            "usage_count": usage_count,
        }
    )


class InMemorySetRepository:
    def __init__(self, sets: list[ProblemSet]) -> None:
        self.sets = {s.id: s for s in sets}

    def get(self, set_id: str) -> ProblemSet | None:
        return self.sets.get(set_id)

    def least_used(self, grade: str) -> ProblemSet | None:
        candidates = [s for s in self.sets.values() if s.grade == grade and s.enabled]
        return min(candidates, key=lambda s: s.usage_count, default=None)


@pytest.fixture
def repo() -> InMemorySetRepository:
    return InMemorySetRepository(
        [
            make_set("pre2_0001", usage_count=2),
            make_set("pre2_0002", usage_count=1),
            make_set("pre2_0003", usage_count=0, enabled=False),
            make_set("2_0001", grade="2", usage_count=0),
        ]
    )


@pytest.fixture
def client(repo: InMemorySetRepository) -> TestClient:
    app = create_app(
        settings=make_settings(),
        token_verifier=fake_verifier,
        set_repository=repo,
        url_signer=fake_signer,
    )
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {VALID_TOKEN}"}
