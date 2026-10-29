from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from eiken_api.models import GradeConfig


def grades(request: Request) -> dict[str, GradeConfig]:
    return request.app.state.grades


Grades = Annotated[dict[str, GradeConfig], Depends(grades)]


def require_grade(grade: str, all_grades: dict[str, GradeConfig]) -> GradeConfig:
    config = all_grades.get(grade)
    if config is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"unknown grade: {grade}")
    return config
