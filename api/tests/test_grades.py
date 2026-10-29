from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from eiken_api.grades import GRADES_DIR, fill_candidate_name, load_grades, parse_grade


def _pre2_raw() -> dict[str, Any]:
    return yaml.safe_load((GRADES_DIR / "pre2.yaml").read_text(encoding="utf-8"))


def test_pre2_matches_exam_format() -> None:
    pre2 = load_grades()["pre2"]
    assert [p.id for p in pre2.parts] == ["silent_reading", "read_aloud", "q1", "q2", "q3", "q4", "q5"]
    assert pre2.max_score == 33
    assert pre2.pass_score == 19
    assert pre2.parts[0].seconds == 20
    assert [p.id for p in pre2.parts if p.follow_up] == ["q4", "q5"]


def test_undefined_phrase_reference_is_rejected() -> None:
    raw = _pre2_raw()
    raw["parts"][0]["cue_phrases"] = ["no_such_phrase"]
    with pytest.raises(ValidationError, match="no_such_phrase"):
        parse_grade(raw)


def test_duplicate_part_id_is_rejected() -> None:
    raw = _pre2_raw()
    raw["parts"][2]["id"] = "read_aloud"
    with pytest.raises(ValidationError, match="duplicate"):
        parse_grade(raw)


def test_unknown_part_type_is_rejected() -> None:
    raw = _pre2_raw()
    raw["parts"][1]["type"] = "singing"
    with pytest.raises(ValidationError):
        parse_grade(raw)


def test_file_name_must_match_grade(tmp_path: Path) -> None:
    (tmp_path / "2.yaml").write_text(yaml.safe_dump(_pre2_raw()), encoding="utf-8")
    with pytest.raises(ValueError, match="expected '2'"):
        load_grades(tmp_path)


def test_fill_candidate_name_handles_strings_and_lists() -> None:
    raw = _pre2_raw()
    raw["phrases"]["greeting"].append("Thank you, {candidate_name}.")
    filled = fill_candidate_name(parse_grade(raw), "Ms. Example")
    assert filled.phrases["turn_over"] == "Now, Ms. Example, please turn over the card and put it down."
    assert filled.phrases["greeting"][-1] == "Thank you, Ms. Example."
