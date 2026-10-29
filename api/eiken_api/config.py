from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    default_grade: str
    gcp_project: str
    gcp_location: str
    assets_bucket: str
    gemini_model: str
    gemini_timeout_sec: int = Field(default=60, gt=0)
    allowed_emails: Annotated[list[str], NoDecode]
    cors_origins: Annotated[list[str], NoDecode]
    signed_url_ttl_sec: int = Field(gt=0)
    candidate_name: str

    @field_validator("allowed_emails", "cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("allowed_emails")
    @classmethod
    def _require_emails(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("ALLOWED_EMAILS must contain at least one address")
        return [email.lower() for email in value]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]
