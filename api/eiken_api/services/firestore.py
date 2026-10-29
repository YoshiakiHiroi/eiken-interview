from typing import Protocol

from eiken_api.models import ProblemSet

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
