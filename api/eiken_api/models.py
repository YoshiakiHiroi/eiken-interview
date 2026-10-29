from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PartType = Literal[
    "silent_reading",
    "read_aloud",
    "passage_question",
    "picture_actions",
    "picture_situation",
    "picture_story",
    "opinion",
    "personal",
]
CardKind = Literal["passage", "picture_a", "picture_b", "none"]
SetMode = Literal["full", "drill_read", "drill_q2", "drill_q3", "drill_q45"]


class GradePart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: PartType
    card: CardKind
    cue_phrases: list[str] = []
    seconds: int | None = Field(default=None, gt=0)
    prep_seconds: int | None = Field(default=None, gt=0)
    question_no: int | None = None
    follow_up: bool = False
    max_score: int = Field(default=0, ge=0)


class GradeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grade: str
    label: str
    test_name: str
    pass_score: int = Field(gt=0)
    attitude_max_score: int = Field(ge=0)
    phrases: dict[str, str | list[str]]
    opening_phrases: list[str] = []
    closing_phrases: list[str] = []
    parts: list[GradePart]

    @property
    def max_score(self) -> int:
        return sum(part.max_score for part in self.parts) + self.attitude_max_score

    @model_validator(mode="after")
    def _check_references(self) -> "GradeConfig":
        part_ids = [part.id for part in self.parts]
        if len(part_ids) != len(set(part_ids)):
            raise ValueError(f"duplicate part ids in grade {self.grade}")
        referenced = set(self.opening_phrases) | set(self.closing_phrases)
        for part in self.parts:
            referenced |= set(part.cue_phrases)
        missing = referenced - self.phrases.keys()
        if missing:
            raise ValueError(f"grade {self.grade} references undefined phrases: {sorted(missing)}")
        if self.pass_score > self.max_score:
            raise ValueError(f"grade {self.grade} pass_score exceeds max_score {self.max_score}")
        return self


class GradeResponse(GradeConfig):
    max_score_total: int


class Passage(BaseModel):
    title: str
    text: str
    key_sentence: str
    audio_model_url: str | None = None


class Question(BaseModel):
    no: int
    type: str
    text: str
    audio_url: str | None = None
    model_answer: str | None = None
    picture_url: str | None = None
    actions: list[str] | None = None
    follow_up_yes: str | None = None
    follow_up_no: str | None = None
    model_answer_yes: str | None = None
    model_answer_no: str | None = None
    follow_up_audio_yes_url: str | None = None
    follow_up_audio_no_url: str | None = None


class ProblemSet(BaseModel):
    id: str
    grade: str
    enabled: bool
    topic: str
    voice: str
    passage: Passage
    questions: list[Question]
    common_audio: dict[str, str] = {}
    usage_count: int = 0
    created_at: datetime | None = None


Clarity = Literal["clear", "somewhat_unclear", "unclear"]
YesNo = Literal["yes", "no"]


# Gemini の response_schema にも使うため、値の範囲チェックは Field 制約ではなく scoring.validate_evaluation で行う
class Evaluation(BaseModel):
    transcript: str
    score: int
    feedback_ja: str
    model_answer: str
    issue_tags: list[str]
    confidence: float
    clarity: Clarity


class AttitudeEvaluation(BaseModel):
    score: int
    feedback_ja: str


class Answer(BaseModel):
    part: str
    audio_url: str
    follow_up_audio_url: str | None = None
    duration_sec: float
    silence_before_sec: float
    replay_count: int
    yes_no: YesNo | None = None
    transcript: str | None = None
    score: int | None = None
    feedback_ja: str | None = None
    model_answer: str | None = None
    issue_tags: list[str] = []
    confidence: float | None = None
    clarity: Clarity | None = None
    evaluation_error: str | None = None


class Attitude(BaseModel):
    score: int | None
    feedback_ja: str | None
    evaluation_error: str | None = None


class Session(BaseModel):
    id: str
    uid: str
    grade: str
    mode: SetMode
    set_id: str
    started_at: datetime
    finished_at: datetime | None = None
    answers: list[Answer] = []
    attitude: Attitude | None = None
    total: int | None = None
    passed: bool | None = None


class CreateSessionRequest(BaseModel):
    mode: SetMode
    set_id: str


class CreateSessionResponse(BaseModel):
    session_id: str
