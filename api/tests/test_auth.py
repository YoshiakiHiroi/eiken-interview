import pytest

from eiken_api.auth import AuthError, User, authorize

ALLOWED = ["owner@example.com"]


def test_authorize_allows_listed_verified_email_case_insensitively() -> None:
    user = authorize({"uid": "u1", "email": "Owner@Example.com", "email_verified": True}, ALLOWED)
    assert user == User(uid="u1", email="owner@example.com")


@pytest.mark.parametrize(
    "claims",
    [
        {"uid": "u1", "email": "owner@example.com", "email_verified": False},
        {"uid": "u1", "email_verified": True},
        {"uid": "u1", "email": "other@example.com", "email_verified": True},
    ],
)
def test_authorize_rejects(claims: dict[str, object]) -> None:
    with pytest.raises(AuthError):
        authorize(claims, ALLOWED)
