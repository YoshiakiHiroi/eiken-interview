from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from eiken_api.auth import TokenVerifier, firebase_verifier
from eiken_api.config import Settings, get_settings
from eiken_api.grades import fill_candidate_name, load_grades
from eiken_api.models import GradeConfig
from eiken_api.routers import evaluate, grades, sessions, sets
from eiken_api.services.firestore import (
    FirestoreSessionRepository,
    FirestoreSetRepository,
    SessionRepository,
    SetRepository,
)
from eiken_api.services.gemini import Evaluator, GeminiEvaluator
from eiken_api.services.storage import AudioStore, GcsAudioStore, UrlSigner, gcs_signer


@dataclass(frozen=True)
class Dependencies:
    token_verifier: TokenVerifier
    set_repository: SetRepository
    session_repository: SessionRepository
    url_signer: UrlSigner
    audio_store: AudioStore
    evaluator: Evaluator


def create_app(
    settings: Settings,
    deps: Dependencies,
    grade_configs: dict[str, GradeConfig] | None = None,
) -> FastAPI:
    all_grades = grade_configs if grade_configs is not None else load_grades()
    if settings.default_grade not in all_grades:
        raise ValueError(f"DEFAULT_GRADE '{settings.default_grade}' has no grade definition")

    app = FastAPI(title="eiken-api")
    app.state.settings = settings
    app.state.token_verifier = deps.token_verifier
    app.state.set_repository = deps.set_repository
    app.state.session_repository = deps.session_repository
    app.state.url_signer = deps.url_signer
    app.state.audio_store = deps.audio_store
    app.state.evaluator = deps.evaluator
    app.state.grades = {key: fill_candidate_name(config, settings.candidate_name) for key, config in all_grades.items()}

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(grades.router)
    app.include_router(sets.router)
    app.include_router(sessions.router)
    app.include_router(evaluate.router)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


def build_app() -> FastAPI:
    settings = get_settings()
    return create_app(
        settings=settings,
        deps=Dependencies(
            token_verifier=firebase_verifier(settings.gcp_project),
            set_repository=FirestoreSetRepository(settings.gcp_project),
            session_repository=FirestoreSessionRepository(settings.gcp_project),
            url_signer=gcs_signer(settings.signed_url_ttl_sec),
            audio_store=GcsAudioStore(settings.gcp_project, settings.assets_bucket),
            evaluator=GeminiEvaluator(
                project=settings.gcp_project,
                location=settings.gemini_location,
                model=settings.gemini_model,
                timeout_sec=settings.gemini_timeout_sec,
            ),
        ),
    )
