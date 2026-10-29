from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from eiken_api.auth import CurrentUser
from eiken_api.models import ProblemSet, SetMode
from eiken_api.routers.deps import Grades, require_grade
from eiken_api.services.firestore import SetRepository
from eiken_api.services.storage import UrlSigner, sign_gs_urls

router = APIRouter(prefix="/api/sets", tags=["sets"])


def _signed(problem_set: ProblemSet, signer: UrlSigner) -> dict[str, Any]:
    return sign_gs_urls(problem_set.model_dump(mode="json"), signer)


@router.get("/next")
def next_set(
    request: Request,
    _: CurrentUser,
    all_grades: Grades,
    grade: str,
    mode: SetMode = "full",
) -> dict[str, Any]:
    require_grade(grade, all_grades)
    repo: SetRepository = request.app.state.set_repository
    problem_set = repo.least_used(grade)
    if problem_set is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"no enabled sets for grade {grade}")
    return _signed(problem_set, request.app.state.url_signer)


@router.get("/{set_id}")
def get_set(request: Request, _: CurrentUser, set_id: str) -> dict[str, Any]:
    repo: SetRepository = request.app.state.set_repository
    problem_set = repo.get(set_id)
    if problem_set is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"set not found: {set_id}")
    return _signed(problem_set, request.app.state.url_signer)
