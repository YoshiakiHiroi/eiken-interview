from collections.abc import Callable
from datetime import timedelta
from typing import Any, Protocol

UrlSigner = Callable[[str], str]

GS_PREFIX = "gs://"
CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"


def split_gs_url(url: str) -> tuple[str, str]:
    if not url.startswith(GS_PREFIX):
        raise ValueError(f"not a gs:// url: {url}")
    bucket, _, blob = url[len(GS_PREFIX) :].partition("/")
    if not bucket or not blob:
        raise ValueError(f"gs:// url must include bucket and object: {url}")
    return bucket, blob


def sign_gs_urls(value: Any, signer: UrlSigner) -> Any:
    if isinstance(value, str):
        return signer(value) if value.startswith(GS_PREFIX) else value
    if isinstance(value, dict):
        return {key: sign_gs_urls(item, signer) for key, item in value.items()}
    if isinstance(value, list):
        return [sign_gs_urls(item, signer) for item in value]
    return value


def gcs_signer(ttl_sec: int) -> UrlSigner:
    import google.auth
    from google.auth.transport.requests import Request
    from google.cloud import storage

    # スコープを明示しないと、ローカルのなりすまし ADC でトークン取得が 400 になる
    credentials, project = google.auth.default(scopes=[CLOUD_PLATFORM_SCOPE])
    client = storage.Client(project=project, credentials=credentials)

    def sign(url: str) -> str:
        bucket_name, blob_name = split_gs_url(url)
        if not credentials.valid:
            credentials.refresh(Request())
        blob = client.bucket(bucket_name).blob(blob_name)
        # Cloud Run の実行 SA は鍵を持たないため、IAM signBlob 経由で署名する
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=ttl_sec),
            method="GET",
            service_account_email=getattr(credentials, "service_account_email", None),
            access_token=getattr(credentials, "token", None),
        )

    return sign


class AudioStore(Protocol):
    def put(self, path: str, data: bytes, content_type: str) -> str: ...


class GcsAudioStore:
    def __init__(self, project: str, bucket: str) -> None:
        from google.cloud import storage

        self._bucket = storage.Client(project=project).bucket(bucket)

    def put(self, path: str, data: bytes, content_type: str) -> str:
        blob = self._bucket.blob(path)
        blob.upload_from_string(data, content_type=content_type)
        return f"{GS_PREFIX}{self._bucket.name}/{path}"
