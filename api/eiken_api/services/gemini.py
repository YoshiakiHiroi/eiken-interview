from collections.abc import Callable, Sequence
from typing import Protocol

from pydantic import BaseModel, ValidationError

from eiken_api.models import AttitudeEvaluation, Evaluation
from eiken_api.services.scoring import EvaluationValidationError, validate_evaluation

MAX_ATTEMPTS = 2


class EvaluationFailed(Exception):
    pass


class Evaluator(Protocol):
    def evaluate_answer(
        self, system_prompt: str, user_prompt: str, audios: Sequence[bytes], max_score: int
    ) -> Evaluation: ...

    def evaluate_attitude(self, prompt: str, max_score: int) -> AttitudeEvaluation: ...


def with_retry[T](call: Callable[[], T], attempts: int = MAX_ATTEMPTS) -> T:
    errors: list[str] = []
    for _ in range(attempts):
        try:
            return call()
        except Exception as exc:  # noqa: BLE001 - API・タイムアウト・JSON 破損のいずれもリトライ対象
            errors.append(f"{type(exc).__name__}: {exc}")
    raise EvaluationFailed("; ".join(errors))


def parse_evaluation(text: str | None, max_score: int) -> Evaluation:
    if not text:
        raise EvaluationValidationError("empty response")
    try:
        evaluation = Evaluation.model_validate_json(text)
    except ValidationError as exc:
        raise EvaluationValidationError(f"invalid evaluation JSON: {exc.error_count()} errors") from exc
    return validate_evaluation(evaluation, max_score)


def parse_attitude(text: str | None, max_score: int) -> AttitudeEvaluation:
    if not text:
        raise EvaluationValidationError("empty response")
    try:
        attitude = AttitudeEvaluation.model_validate_json(text)
    except ValidationError as exc:
        raise EvaluationValidationError(f"invalid attitude JSON: {exc.error_count()} errors") from exc
    if not 0 <= attitude.score <= max_score:
        raise EvaluationValidationError(f"attitude score {attitude.score} is outside 0..{max_score}")
    return attitude


class GeminiEvaluator:
    def __init__(self, project: str, location: str, model: str, timeout_sec: int) -> None:
        from google import genai
        from google.genai import types

        self._types = types
        self._model = model
        self._client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
            http_options=types.HttpOptions(timeout=timeout_sec * 1000),
        )

    def _generate(self, contents: list[object], schema: type[BaseModel], system_prompt: str | None) -> str | None:
        config = self._types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.2,
        )
        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,  # pyright: ignore[reportArgumentType]
            config=config,
        )
        return response.text

    def evaluate_answer(
        self, system_prompt: str, user_prompt: str, audios: Sequence[bytes], max_score: int
    ) -> Evaluation:
        parts: list[object] = []
        for index, audio in enumerate(audios, start=1):
            parts.append(self._types.Part.from_text(text=f"音声{index}:"))
            parts.append(self._types.Part.from_bytes(data=audio, mime_type="audio/wav"))
        parts.append(self._types.Part.from_text(text=user_prompt))
        return with_retry(lambda: parse_evaluation(self._generate(parts, Evaluation, system_prompt), max_score))

    def evaluate_attitude(self, prompt: str, max_score: int) -> AttitudeEvaluation:
        return with_retry(lambda: parse_attitude(self._generate([prompt], AttitudeEvaluation, None), max_score))
