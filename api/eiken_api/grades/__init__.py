from pathlib import Path

import yaml

from eiken_api.models import GradeConfig

GRADES_DIR = Path(__file__).parent


def parse_grade(raw: object) -> GradeConfig:
    return GradeConfig.model_validate(raw)


def load_grades(directory: Path = GRADES_DIR) -> dict[str, GradeConfig]:
    grades: dict[str, GradeConfig] = {}
    for path in sorted(directory.glob("*.yaml")):
        config = parse_grade(yaml.safe_load(path.read_text(encoding="utf-8")))
        if config.grade != path.stem:
            raise ValueError(f"{path.name} declares grade '{config.grade}', expected '{path.stem}'")
        grades[config.grade] = config
    if not grades:
        raise ValueError(f"no grade definitions found in {directory}")
    return grades


def fill_candidate_name(config: GradeConfig, candidate_name: str) -> GradeConfig:
    def fill(value: str | list[str]) -> str | list[str]:
        if isinstance(value, str):
            return value.replace("{candidate_name}", candidate_name)
        return [item.replace("{candidate_name}", candidate_name) for item in value]

    return config.model_copy(update={"phrases": {key: fill(value) for key, value in config.phrases.items()}})
