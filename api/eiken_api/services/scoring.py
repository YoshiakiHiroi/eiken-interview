from collections.abc import Sequence
from dataclasses import dataclass

from eiken_api.models import Answer, Evaluation, GradeConfig, GradePart, ProblemSet, Question, YesNo

ISSUE_TAGS = frozenset(
    {
        "missing_be_verb",
        "wrong_tense",
        "third_person_s",
        "article_error",
        "plural_error",
        "no_reason_given",
        "only_one_sentence",
        "off_topic",
        "too_short",
        "long_silence",
        "japanese_used",
        "unclear_pronunciation",
        "missing_person",
        "not_progressive",
        "no_because",
        "yes_no_mismatch",
    }
)
MISPRONUNCIATION_PREFIX = "mispronunciation:"


class EvaluationValidationError(ValueError):
    pass


def normalize_issue_tags(tags: Sequence[str]) -> list[str]:
    normalized: list[str] = []
    for raw in tags:
        tag = raw.strip().lower()
        if tag.startswith(MISPRONUNCIATION_PREFIX):
            word = tag[len(MISPRONUNCIATION_PREFIX) :].strip()
            tag = f"{MISPRONUNCIATION_PREFIX}{word}" if word else ""
        elif tag not in ISSUE_TAGS:
            tag = ""
        if tag and tag not in normalized:
            normalized.append(tag)
    return normalized


def validate_evaluation(evaluation: Evaluation, max_score: int) -> Evaluation:
    if not 0 <= evaluation.score <= max_score:
        raise EvaluationValidationError(f"score {evaluation.score} is outside 0..{max_score}")
    if not 0.0 <= evaluation.confidence <= 1.0:
        raise EvaluationValidationError(f"confidence {evaluation.confidence} is outside 0..1")
    return evaluation.model_copy(update={"issue_tags": normalize_issue_tags(evaluation.issue_tags)})


def scorable_parts(grade: GradeConfig) -> list[GradePart]:
    return [part for part in grade.parts if part.max_score > 0]


def find_part(grade: GradeConfig, part_id: str) -> GradePart | None:
    return next((part for part in scorable_parts(grade) if part.id == part_id), None)


def find_question(problem_set: ProblemSet, part: GradePart) -> Question | None:
    if part.question_no is None:
        return None
    return next((q for q in problem_set.questions if q.no == part.question_no), None)


def follow_up_question(question: Question | None, yes_no: YesNo | None) -> str:
    if question is None or yes_no is None:
        return ""
    return (question.follow_up_yes if yes_no == "yes" else question.follow_up_no) or ""


def build_prompt_context(
    grade: GradeConfig,
    part: GradePart,
    problem_set: ProblemSet,
    yes_no: YesNo | None,
) -> dict[str, str]:
    question = find_question(problem_set, part)
    if question is None:
        model_answer = ""
    elif yes_no == "yes":
        model_answer = question.model_answer_yes or ""
    elif yes_no == "no":
        model_answer = question.model_answer_no or ""
    else:
        model_answer = question.model_answer or ""
    actions = question.actions if question and question.actions else []
    return {
        "grade_label": grade.label,
        "test_name": grade.test_name,
        "max_score": str(part.max_score),
        "passage_title": problem_set.passage.title,
        "passage_text": problem_set.passage.text,
        "key_sentence": problem_set.passage.key_sentence,
        "question_text": question.text if question else "",
        "follow_up_question": follow_up_question(question, yes_no),
        "yes_no": yes_no or "",
        "reference_answer": model_answer,
        "actions": "\n".join(f"- {action}" for action in actions),
        "action_count": str(len(actions)),
    }


@dataclass(frozen=True)
class Totals:
    total: int | None
    passed: bool | None


def compute_totals(
    grade: GradeConfig,
    answers: Sequence[Answer],
    attitude_score: int | None,
    full_mode: bool,
) -> Totals:
    """Sum scores; total is None unless every scorable part (and attitude in full mode) has a score."""
    by_part = {answer.part: answer for answer in answers}
    expected = [part.id for part in scorable_parts(grade)] if full_mode else list(by_part)
    scores = [by_part[part_id].score if part_id in by_part else None for part_id in expected]
    if full_mode:
        scores.append(attitude_score)
    if any(score is None for score in scores):
        return Totals(total=None, passed=None)
    total = sum(score for score in scores if score is not None)
    return Totals(total=total, passed=total >= grade.pass_score if full_mode else None)
