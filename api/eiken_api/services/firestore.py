from typing import Protocol

from eiken_api.models import ProblemSet, Session

SETS_COLLECTION = "sets"


class SetRepository(Protocol):
    def get(self, set_id: str) -> ProblemSet | None: ...

    def least_used(self, grade: str) -> ProblemSet | None: ...


class FirestoreSetRepository:
    def __init__(self, project: str) -> None:
        from google.cloud import firestore

        self._client = firestore.Client(project=project)

    def get(self, set_id: str) -> ProblemSet | None:
        snapshot = self._client.collection(SETS_COLLECTION).document(set_id).get()
        if not snapshot.exists:
            return None
        return ProblemSet.model_validate(snapshot.to_dict())

    def least_used(self, grade: str) -> ProblemSet | None:
        from google.cloud.firestore_v1.base_query import FieldFilter

        query = (
            self._client.collection(SETS_COLLECTION)
            .where(filter=FieldFilter("grade", "==", grade))
            .where(filter=FieldFilter("enabled", "==", True))
            .order_by("usage_count")
            .limit(1)
        )
        for snapshot in query.stream():
            return ProblemSet.model_validate(snapshot.to_dict())
        return None


SESSIONS_COLLECTION = "sessions"


class SessionRepository(Protocol):
    def new_id(self) -> str: ...

    def get(self, session_id: str) -> Session | None: ...

    def save(self, session: Session) -> None: ...


class FirestoreSessionRepository:
    def __init__(self, project: str) -> None:
        from google.cloud import firestore

        self._collection = firestore.Client(project=project).collection(SESSIONS_COLLECTION)

    def new_id(self) -> str:
        return self._collection.document().id

    def get(self, session_id: str) -> Session | None:
        snapshot = self._collection.document(session_id).get()
        if not snapshot.exists:
            return None
        return Session.model_validate(snapshot.to_dict())

    def save(self, session: Session) -> None:
        self._collection.document(session.id).set(session.model_dump())
