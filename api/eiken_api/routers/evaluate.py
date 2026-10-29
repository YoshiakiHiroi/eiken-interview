from typing import Annotated, Any

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile, status
from starlette.concurrency import run_in_threadpool

from eiken_api.auth import CurrentUser
from eiken_api.models import YesNo
from eiken_api.routers.deps import Grades, require_grade
from eiken_api.routers.sessions import load_owned_session
from eiken_api.services.audio import AudioConversionError
from eiken_api.services.firestore import SetRepository
from eiken_api.services.scoring import find_part
from eiken_api.services.sessions import AnswerInput, AnswerRejected, evaluate_answer, finish_session
from eiken_api.services.storage import sign_gs_urls

MAX_AUDIO_BYTES = 10 * 1024 * 1024

router = APIRouter(prefix="/api/sessions", tags=["evaluate"])


async def _read_audio(upload: UploadFile) -> bytes:
    data = await upload.read(MAX_AUDIO_BYTES + 1)
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, f"{upload.filename} exceeds {MAX_AUDIO_BYTES} bytes")
    return data


@router.post("/{session_id}/answers/{part_id}")
async def submit_answer(
    request: Request,
    user: CurrentUser,
    all_grades: Grades,
    session_id: str,
    part_id: str,
    audio: UploadFile,
    duration_sec: Annotated[float, Form(ge=0)],
    silence_before_sec: Annotated[float, Form(ge=0)],
    replay_count: Annotated[int, Form(ge=0)],
    yes_no: Annotated[YesNo | None, Form()] = None,
    follow_up_audio: UploadFile | None = None,
) -> dict[str, Any]:
    session = load_owned_session(request, user, session_id)
    grade = require_grade(session.grade, all_grades)
    part = find_part(grade, part_id)
    if part is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"part {part_id} is not scored in grade {grade.grade}")
    set_repo: SetRepository = request.app.state.set_repository
    problem_set = set_repo.get(session.set_id)
    if problem_set is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"set not found: {session.set_id}")

    answer = AnswerInput(
        audio=await _read_audio(audio),
        follow_up_audio=await _read_audio(follow_up_audio) if follow_up_audio else None,
        duration_sec=duration_sec,
        silence_before_sec=silence_before_sec,
        replay_count=replay_count,
        yes_no=yes_no,
    )
    try:
        record = await run_in_threadpool(
            evaluate_answer,
            session=session,
            grade=grade,
            part=part,
            problem_set=problem_set,
            answer=answer,
            audio_store=request.app.state.audio_store,
            evaluator=request.app.state.evaluator,
            sessions=request.app.state.session_repository,
        )
    except (AnswerRejected, AudioConversionError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    return sign_gs_urls(record.model_dump(mode="json"), request.app.state.url_signer)


@router.post("/{session_id}/finish")
def finish(request: Request, user: CurrentUser, all_grades: Grades, session_id: str) -> dict[str, Any]:
    session = load_owned_session(request, user, session_id)
    grade = require_grade(session.grade, all_grades)
    finished = finish_session(
        session=session,
        grade=grade,
        evaluator=request.app.state.evaluator,
        sessions=request.app.state.session_repository,
    )
    return sign_gs_urls(finished.model_dump(mode="json"), request.app.state.url_signer)
