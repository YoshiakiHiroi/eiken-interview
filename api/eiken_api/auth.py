from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

TokenVerifier = Callable[[str], Mapping[str, Any]]


@dataclass(frozen=True)
class User:
    uid: str
    email: str


class AuthError(Exception):
    pass


def authorize(claims: Mapping[str, Any], allowed_emails: list[str]) -> User:
    email = str(claims.get("email", "")).lower()
    if not email or not claims.get("email_verified", False):
        raise AuthError("email is missing or not verified")
    if email not in allowed_emails:
        raise AuthError("email is not allowed")
    return User(uid=str(claims["uid"]), email=email)


def firebase_verifier(project_id: str) -> TokenVerifier:
    import firebase_admin
    from firebase_admin import auth

    app = firebase_admin.initialize_app(options={"projectId": project_id})

    def verify(token: str) -> Mapping[str, Any]:
        return auth.verify_id_token(token, app=app)

    return verify


_bearer = HTTPBearer(auto_error=False)


def current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    verifier: TokenVerifier = request.app.state.token_verifier
    try:
        claims = verifier(credentials.credentials)
    except Exception as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token") from exc
    try:
        return authorize(claims, request.app.state.settings.allowed_emails)
    except AuthError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc


CurrentUser = Annotated[User, Depends(current_user)]
