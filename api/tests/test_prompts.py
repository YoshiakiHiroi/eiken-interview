from pathlib import Path

import pytest
from conftest import make_set

from eiken_api.grades import load_grades
from eiken_api.services.prompts import (
    ATTITUDE_PROMPT,
    SYSTEM_PROMPT,
    PromptError,
    prompt_name_for,
    render_prompt,
)
from eiken_api.services.scoring import build_prompt_context, scorable_parts


def test_every_scored_part_of_every_grade_renders_without_missing_variables() -> None:
    for grade in load_grades().values():
        for part in scorable_parts(grade):
            context = build_prompt_context(grade, part, make_set("x"), "yes" if part.follow_up else None)
            assert "$" not in render_prompt(SYSTEM_PROMPT, context)
            assert "$" not in render_prompt(prompt_name_for(part.type), context)


def test_attitude_prompt_renders() -> None:
    text = render_prompt(
        ATTITUDE_PROMPT, {"grade_label": "準2級", "test_name": "Grade Pre-2", "max_score": "3", "answers": "[]"}
    )
    assert "0〜3" in text


def test_missing_variable_is_reported(tmp_path: Path) -> None:
    (tmp_path / "p.md").write_text("Hello ${name}", encoding="utf-8")
    with pytest.raises(PromptError, match="name"):
        render_prompt("p", {}, directory=tmp_path)


def test_unsupported_part_type_is_reported() -> None:
    with pytest.raises(PromptError, match="picture_story"):
        prompt_name_for("picture_story")
