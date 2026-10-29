from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from eiken_api.auth import CurrentUser, User
from eiken_api.models import CreateSessionRequest, CreateSessionResponse, Session
from eiken_api.routers.deps import Grades, require_grade
from eiken_api.services.firestore import SessionRepository, SetRepository
from eiken_api.services.storage import sign_gs_urls

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def load_owned_session(request: Request, user: User, session_id: str) -> Session:
    repo: SessionRepository = request.app.state.session_repository
    session = repo.get(session_id)
    if session is None or session.uid != user.uid:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"session not found: {session_id}")
    return session


@router.post("", status_code=status.HTTP_201_CREATED)
def create_session(
    request: Request, user: CurrentUser, all_grades: Grades, body: CreateSessionRequest
) -> CreateSessionResponse:
    set_repo: SetRepository = request.app.state.set_repository
    problem_set = set_repo.get(body.set_id)
    if problem_set is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"set not found: {body.set_id}")
    require_grade(problem_set.grade, all_grades)

    repo: SessionRepository = request.app.state.session_repository
    session = Session(
        id=repo.new_id(),
        uid=user.uid,
        grade=problem_set.grade,
        mode=body.mode,
        set_id=problem_set.id,
        started_at=datetime.now(UTC),
    )
    repo.save(session)
    return CreateSessionResponse(session_id=session.id)


@router.get("/{session_id}")
def get_session(request: Request, user: CurrentUser, session_id: str) -> dict[str, Any]:
    session = load_owned_session(request, user, session_id)
    return sign_gs_urls(session.model_dump(mode="json"), request.app.state.url_signer)
