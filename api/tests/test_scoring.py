import pytest
from conftest import make_set

from eiken_api.grades import load_grades
from eiken_api.models import Answer, Evaluation, GradeConfig
from eiken_api.services.scoring import (
    EvaluationValidationError,
    build_prompt_context,
    compute_totals,
    find_part,
    normalize_issue_tags,
    validate_evaluation,
)


@pytest.fixture
def pre2() -> GradeConfig:
    return load_grades()["pre2"]


def _answer(part: str, score: int | None) -> Answer:
    return Answer(
        part=part, audio_url="gs://b/x.wav", duration_sec=5, silence_before_sec=1, replay_count=0, score=score
    )


def _evaluation(**overrides: object) -> Evaluation:
    values: dict[str, object] = {
        "transcript": "t",
        "score": 3,
        "feedback_ja": "f",
        "model_answer": "m",
        "issue_tags": [],
        "confidence": 0.5,
        "clarity": "clear",
    }
    values.update(overrides)
    return Evaluation.model_validate(values)


def test_normalize_issue_tags_drops_unknown_and_duplicates() -> None:
    tags = ["third_person_s", "made_up", " Mispronunciation:Recycle ", "third_person_s", "mispronunciation:"]
    assert normalize_issue_tags(tags) == ["third_person_s", "mispronunciation:recycle"]


@pytest.mark.parametrize(("score", "confidence"), [(-1, 0.5), (6, 0.5), (3, 1.5)])
def test_validate_evaluation_rejects_out_of_range(score: int, confidence: float) -> None:
    with pytest.raises(EvaluationValidationError):
        validate_evaluation(_evaluation(score=score, confidence=confidence), max_score=5)


def test_validate_evaluation_normalizes_tags() -> None:
    result = validate_evaluation(_evaluation(issue_tags=["bogus", "no_because"]), max_score=5)
    assert result.issue_tags == ["no_because"]


def test_only_scored_parts_are_answerable(pre2: GradeConfig) -> None:
    assert find_part(pre2, "q2") is not None
    assert find_part(pre2, "silent_reading") is None
    assert find_part(pre2, "q9") is None


def test_build_prompt_context_uses_yes_no_branch(pre2: GradeConfig) -> None:
    part = find_part(pre2, "q4")
    assert part is not None
    context = build_prompt_context(pre2, part, make_set("pre2_0001"), "no")
    assert context["follow_up_question"] == "Why not?"
    assert context["reference_answer"] == "No, I don't. Many people are too busy."
    assert context["grade_label"] == "準2級"


def test_build_prompt_context_lists_actions(pre2: GradeConfig) -> None:
    part = find_part(pre2, "q2")
    assert part is not None
    context = build_prompt_context(pre2, part, make_set("pre2_0001"), None)
    assert context["actions"] == "- A man is carrying a box.\n- A woman is watering flowers."
    assert context["action_count"] == "2"


def test_compute_totals_full_mode(pre2: GradeConfig) -> None:
    answers = [_answer(p, 3) for p in ["read_aloud", "q1", "q2", "q3", "q4", "q5"]]
    assert compute_totals(pre2, answers, attitude_score=2, full_mode=True).total == 20
    assert compute_totals(pre2, answers, attitude_score=2, full_mode=True).passed is True
    assert compute_totals(pre2, answers, attitude_score=0, full_mode=True).passed is False


def test_compute_totals_full_mode_needs_every_score(pre2: GradeConfig) -> None:
    answers = [_answer(p, 3) for p in ["read_aloud", "q1", "q2", "q3", "q4"]] + [_answer("q5", None)]
    totals = compute_totals(pre2, answers, attitude_score=3, full_mode=True)
    assert (totals.total, totals.passed) == (None, None)
    assert compute_totals(pre2, answers[:5], attitude_score=3, full_mode=True).total is None
    assert (
        compute_totals(pre2, [_answer(p, 3) for p in ["read_aloud", "q1", "q2", "q3", "q4", "q5"]], None, True).total
        is None
    )


def test_compute_totals_drill_mode_sums_answered_parts_without_pass_judgement(pre2: GradeConfig) -> None:
    totals = compute_totals(pre2, [_answer("q2", 4), _answer("q3", 2)], attitude_score=None, full_mode=False)
    assert (totals.total, totals.passed) == (6, None)
