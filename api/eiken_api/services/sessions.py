import json
from dataclasses import dataclass
from datetime import UTC, datetime

from eiken_api.models import Answer, Attitude, GradeConfig, GradePart, ProblemSet, Session, YesNo
from eiken_api.services.audio import to_wav
from eiken_api.services.firestore import SessionRepository
from eiken_api.services.gemini import EvaluationFailed, Evaluator
from eiken_api.services.prompts import ATTITUDE_PROMPT, SYSTEM_PROMPT, prompt_name_for, render_prompt
from eiken_api.services.scoring import build_prompt_context, compute_totals
from eiken_api.services.storage import AudioStore


class AnswerRejected(ValueError):
    pass


@dataclass(frozen=True)
class AnswerInput:
    audio: bytes
    follow_up_audio: bytes | None
    duration_sec: float
    silence_before_sec: float
    replay_count: int
    yes_no: YesNo | None


def check_answer_input(part: GradePart, answer: AnswerInput) -> None:
    if part.follow_up and answer.yes_no is None:
        raise AnswerRejected(f"part {part.id} requires yes_no")
    if not part.follow_up and (answer.yes_no is not None or answer.follow_up_audio is not None):
        raise AnswerRejected(f"part {part.id} does not take yes_no or follow_up_audio")


def upsert_answer(answers: list[Answer], answer: Answer) -> list[Answer]:
    return [existing for existing in answers if existing.part != answer.part] + [answer]


def with_totals(session: Session, grade: GradeConfig) -> Session:
    attitude_score = session.attitude.score if session.attitude else None
    totals = compute_totals(grade, session.answers, attitude_score, full_mode=session.mode == "full")
    return session.model_copy(update={"total": totals.total, "passed": totals.passed})


def evaluate_answer(
    *,
    session: Session,
    grade: GradeConfig,
    part: GradePart,
    problem_set: ProblemSet,
    answer: AnswerInput,
    audio_store: AudioStore,
    evaluator: Evaluator,
    sessions: SessionRepository,
) -> Answer:
    check_answer_input(part, answer)
    wavs = [to_wav(answer.audio)]
    if answer.follow_up_audio is not None:
        wavs.append(to_wav(answer.follow_up_audio))

    base = f"sessions/{session.id}/{part.id}"
    audio_url = audio_store.put(f"{base}.wav", wavs[0], "audio/wav")
    follow_up_url = audio_store.put(f"{base}_follow_up.wav", wavs[1], "audio/wav") if len(wavs) > 1 else None

    context = build_prompt_context(grade, part, problem_set, answer.yes_no)
    record = Answer(
        part=part.id,
        audio_url=audio_url,
        follow_up_audio_url=follow_up_url,
        duration_sec=answer.duration_sec,
        silence_before_sec=answer.silence_before_sec,
        replay_count=answer.replay_count,
        yes_no=answer.yes_no,
    )
    try:
        evaluation = evaluator.evaluate_answer(
            system_prompt=render_prompt(SYSTEM_PROMPT, context),
            user_prompt=render_prompt(prompt_name_for(part.type), context),
            audios=wavs,
            max_score=part.max_score,
        )
        record = record.model_copy(update=evaluation.model_dump())
    except EvaluationFailed as exc:
        record = record.model_copy(update={"evaluation_error": str(exc)})

    updated = session.model_copy(update={"answers": upsert_answer(session.answers, record)})
    if updated.finished_at is not None:
        updated = with_totals(updated, grade)
    sessions.save(updated)
    return record


def attitude_answers_summary(session: Session) -> str:
    rows = [
        {
            "part": a.part,
            "silence_before_sec": a.silence_before_sec,
            "duration_sec": a.duration_sec,
            "replay_count": a.replay_count,
            "clarity": a.clarity,
            "transcript": a.transcript,
        }
        for a in session.answers
    ]
    return json.dumps(rows, ensure_ascii=False, indent=2)


def finish_session(
    *,
    session: Session,
    grade: GradeConfig,
    evaluator: Evaluator,
    sessions: SessionRepository,
    now: datetime | None = None,
) -> Session:
    attitude: Attitude | None = None
    if session.mode == "full":
        prompt = render_prompt(
            ATTITUDE_PROMPT,
            {
                "grade_label": grade.label,
                "test_name": grade.test_name,
                "max_score": str(grade.attitude_max_score),
                "answers": attitude_answers_summary(session),
            },
        )
        try:
            result = evaluator.evaluate_attitude(prompt, grade.attitude_max_score)
            attitude = Attitude(score=result.score, feedback_ja=result.feedback_ja)
        except EvaluationFailed as exc:
            attitude = Attitude(score=None, feedback_ja=None, evaluation_error=str(exc))

    finished = session.model_copy(update={"attitude": attitude, "finished_at": now or datetime.now(UTC)})
    finished = with_totals(finished, grade)
    sessions.save(finished)
    return finished
