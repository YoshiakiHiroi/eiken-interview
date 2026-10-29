import json

import pytest

from eiken_api.services.gemini import EvaluationFailed, parse_attitude, parse_evaluation, with_retry
from eiken_api.services.scoring import EvaluationValidationError

VALID = {
    "transcript": "A man is carrying a box.",
    "score": 4,
    "feedback_ja": "良いです。",
    "model_answer": "A man is carrying a box.",
    "issue_tags": ["missing_person", "bogus"],
    "confidence": 0.8,
    "clarity": "clear",
}


def test_with_retry_returns_second_attempt() -> None:
    attempts: list[int] = []

    def flaky() -> str:
        attempts.append(1)
        if len(attempts) == 1:
            raise TimeoutError("slow")
        return "ok"

    assert with_retry(flaky) == "ok"
    assert len(attempts) == 2


def test_with_retry_gives_up_after_two_attempts() -> None:
    attempts: list[int] = []

    def broken() -> str:
        attempts.append(1)
        raise ValueError("broken json")

    with pytest.raises(EvaluationFailed, match="broken json"):
        with_retry(broken)
    assert len(attempts) == 2


def test_parse_evaluation_validates_and_normalizes() -> None:
    assert parse_evaluation(json.dumps(VALID), max_score=5).issue_tags == ["missing_person"]


@pytest.mark.parametrize(
    "text",
    [None, "", "{not json", json.dumps({**VALID, "score": 9}), json.dumps({**VALID, "clarity": "loud"})],
)
def test_parse_evaluation_rejects_bad_output(text: str | None) -> None:
    with pytest.raises(EvaluationValidationError):
        parse_evaluation(text, max_score=5)


def test_parse_attitude_checks_range() -> None:
    assert parse_attitude('{"score": 2, "feedback_ja": "x"}', max_score=3).score == 2
    with pytest.raises(EvaluationValidationError):
        parse_attitude('{"score": 4, "feedback_ja": "x"}', max_score=3)
