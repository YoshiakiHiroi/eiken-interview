from fastapi import APIRouter

from eiken_api.auth import CurrentUser
from eiken_api.models import GradeResponse
from eiken_api.routers.deps import Grades

router = APIRouter(prefix="/api/grades", tags=["grades"])


@router.get("")
def list_grades(_: CurrentUser, all_grades: Grades) -> list[GradeResponse]:
    return [GradeResponse(**config.model_dump(), max_score_total=config.max_score) for config in all_grades.values()]
