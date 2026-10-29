import pytest
from conftest import make_settings
from pydantic import ValidationError

from eiken_api.config import Settings


def test_csv_values_are_split_and_emails_lowercased() -> None:
    settings = make_settings(allowed_emails="A@x.com, b@x.com", cors_origins="http://a,http://b")
    assert settings.allowed_emails == ["a@x.com", "b@x.com"]
    assert settings.cors_origins == ["http://a", "http://b"]


def test_empty_allowlist_is_rejected() -> None:
    with pytest.raises(ValidationError, match="ALLOWED_EMAILS"):
        make_settings(allowed_emails=" , ")


def test_missing_required_value_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ["DEFAULT_GRADE", "GCP_PROJECT", "CANDIDATE_NAME"]:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # pyright: ignore[reportCallIssue]
