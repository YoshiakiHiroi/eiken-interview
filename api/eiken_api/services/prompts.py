from pathlib import Path
from string import Template

from eiken_api.models import PartType

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

PROMPT_BY_PART_TYPE: dict[PartType, str] = {
    "read_aloud": "evaluate_read_aloud",
    "passage_question": "evaluate_passage_question",
    "picture_actions": "evaluate_picture_actions",
    "picture_situation": "evaluate_picture_situation",
    "opinion": "evaluate_opinion_personal",
    "personal": "evaluate_opinion_personal",
}
SYSTEM_PROMPT = "system"
ATTITUDE_PROMPT = "evaluate_attitude"


class PromptError(Exception):
    pass


def prompt_name_for(part_type: PartType) -> str:
    name = PROMPT_BY_PART_TYPE.get(part_type)
    if name is None:
        raise PromptError(f"no evaluation prompt for part type '{part_type}'")
    return name


def render_prompt(name: str, context: dict[str, str], directory: Path = PROMPTS_DIR) -> str:
    path = directory / f"{name}.md"
    if not path.is_file():
        raise PromptError(f"prompt file not found: {path.name}")
    try:
        return Template(path.read_text(encoding="utf-8")).substitute(context)
    except KeyError as exc:
        raise PromptError(f"prompt {path.name} needs variable {exc.args[0]}") from exc
