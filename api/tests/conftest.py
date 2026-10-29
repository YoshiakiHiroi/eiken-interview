import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from eiken_api.config import Settings
from eiken_api.main import Dependencies, create_app
from eiken_api.models import AttitudeEvaluation, Evaluation, ProblemSet, Session
from eiken_api.services.gemini import EvaluationFailed

ALLOWED_EMAIL = "owner@example.com"
VALID_TOKEN = "valid-token"
OUTSIDER_TOKEN = "outsider-token"


def make_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "default_grade": "pre2",
        "gcp_project": "test-project",
        "gcp_location": "asia-northeast1",
        "assets_bucket": "test-bucket",
        "gemini_model": "test-model",
        "gemini_location": "global",
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
    base = f"gs://test-bucket/sets/{set_id}"
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
                "audio_model_url": f"{base}/passage_model.mp3",
            },
            "questions": [
                {
                    "no": 1,
                    "type": "passage",
                    "text": "According to the passage, how can people reduce waste?",
                    "model_answer": "By recycling, they can reduce waste.",
                    "audio_url": f"{base}/q1.mp3",
                },
                {
                    "no": 2,
                    "type": "picture_a",
                    "text": "Please look at the picture and describe the situation.",
                    "actions": ["A man is carrying a box.", "A woman is watering flowers."],
                },
                {
                    "no": 3,
                    "type": "picture_b",
                    "text": "Now, look at the woman in Picture B. Please describe the situation.",
                    "model_answer": "She wants to open the door, but she can't because her hands are full.",
                },
                {
                    "no": 4,
                    "type": "opinion",
                    "text": "Do you think more people will recycle in the future?",
                    "follow_up_yes": "Why?",
                    "follow_up_no": "Why not?",
                    "model_answer_yes": "Yes, I do. Recycling is becoming easier.",
                    "model_answer_no": "No, I don't. Many people are too busy.",
                },
                {
                    "no": 5,
                    "type": "personal",
                    "text": "Do you often cook at home?",
                    "follow_up_yes": "Please tell me more.",
                    "follow_up_no": "Why not?",
                },
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


class InMemorySessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}
        self._counter = 0

    def new_id(self) -> str:
        self._counter += 1
        return f"s{self._counter}"

    def get(self, session_id: str) -> Session | None:
        return self.sessions.get(session_id)

    def save(self, session: Session) -> None:
        self.sessions[session.id] = session


class InMemoryAudioStore:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put(self, path: str, data: bytes, content_type: str) -> str:
        self.objects[path] = data
        return f"gs://test-bucket/{path}"


@dataclass
class FakeEvaluator:
    score: int = 4
    fail: bool = False
    attitude_score: int = 3
    calls: list[dict[str, Any]] = field(default_factory=list)

    def evaluate_answer(
        self, system_prompt: str, user_prompt: str, audios: Sequence[bytes], max_score: int
    ) -> Evaluation:
        self.calls.append({"system": system_prompt, "user": user_prompt, "audios": len(audios), "max": max_score})
        if self.fail:
            raise EvaluationFailed("model returned broken JSON")
        return Evaluation(
            transcript="A man is carrying a box.",
            score=self.score,
            feedback_ja="良い点があります。改善点もあります。",
            model_answer="A man is carrying a box.",
            issue_tags=["missing_person"],
            confidence=0.9,
            clarity="clear",
        )

    def evaluate_attitude(self, prompt: str, max_score: int) -> AttitudeEvaluation:
        self.calls.append({"attitude": prompt, "max": max_score})
        if self.fail:
            raise EvaluationFailed("timeout")
        return AttitudeEvaluation(score=self.attitude_score, feedback_ja="はっきり話せています。")


@dataclass
class Fakes:
    sets: InMemorySetRepository
    sessions: InMemorySessionRepository
    audio: InMemoryAudioStore
    evaluator: FakeEvaluator

    def deps(self) -> Dependencies:
        return Dependencies(
            token_verifier=fake_verifier,
            set_repository=self.sets,
            session_repository=self.sessions,
            url_signer=fake_signer,
            audio_store=self.audio,
            evaluator=self.evaluator,
        )


@pytest.fixture
def fakes() -> Fakes:
    return Fakes(
        sets=InMemorySetRepository(
            [
                make_set("pre2_0001", usage_count=2),
                make_set("pre2_0002", usage_count=1),
                make_set("pre2_0003", usage_count=0, enabled=False),
                make_set("2_0001", grade="2", usage_count=0),
            ]
        ),
        sessions=InMemorySessionRepository(),
        audio=InMemoryAudioStore(),
        evaluator=FakeEvaluator(),
    )


@pytest.fixture
def client(fakes: Fakes) -> TestClient:
    return TestClient(create_app(settings=make_settings(), deps=fakes.deps()))


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {VALID_TOKEN}"}


FFMPEG_ENCODINGS = {
    "webm": ["-c:a", "libopus", "-f", "webm"],
    "ogg": ["-c:a", "libopus", "-f", "ogg"],
    "mp4": ["-c:a", "aac", "-f", "mp4"],
}


@pytest.fixture(scope="session")
def audio_samples(tmp_path_factory: pytest.TempPathFactory) -> dict[str, bytes]:
    if shutil.which("ffmpeg") is None:
        pytest.fail("ffmpeg is required for audio tests")
    directory: Path = tmp_path_factory.mktemp("audio")
    samples: dict[str, bytes] = {}
    for ext, codec in FFMPEG_ENCODINGS.items():
        path = directory / f"tone.{ext}"
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1"]
            + ["-ac", "2", "-ar", "48000", *codec, str(path)],
            check=True,
        )
        samples[ext] = path.read_bytes()
    return samples
