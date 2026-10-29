from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from eiken_api.auth import TokenVerifier, firebase_verifier
from eiken_api.config import Settings, get_settings
from eiken_api.grades import fill_candidate_name, load_grades
from eiken_api.models import GradeConfig
from eiken_api.routers import grades, sets
from eiken_api.services.firestore import FirestoreSetRepository, SetRepository
from eiken_api.services.storage import UrlSigner, gcs_signer


def create_app(
    settings: Settings,
    token_verifier: TokenVerifier,
    set_repository: SetRepository,
    url_signer: UrlSigner,
    grade_configs: dict[str, GradeConfig] | None = None,
) -> FastAPI:
    all_grades = grade_configs if grade_configs is not None else load_grades()
    if settings.default_grade not in all_grades:
        raise ValueError(f"DEFAULT_GRADE '{settings.default_grade}' has no grade definition")

    app = FastAPI(title="eiken-api")
    app.state.settings = settings
    app.state.token_verifier = token_verifier
    app.state.set_repository = set_repository
    app.state.url_signer = url_signer
    app.state.grades = {key: fill_candidate_name(config, settings.candidate_name) for key, config in all_grades.items()}

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(grades.router)
    app.include_router(sets.router)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


def build_app() -> FastAPI:
    settings = get_settings()
    return create_app(
        settings=settings,
        token_verifier=firebase_verifier(settings.gcp_project),
        set_repository=FirestoreSetRepository(settings.gcp_project),
        url_signer=gcs_signer(settings.signed_url_ttl_sec),
    )
