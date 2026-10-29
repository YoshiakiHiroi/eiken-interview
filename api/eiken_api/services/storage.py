from collections.abc import Callable
from datetime import timedelta
from typing import Any

UrlSigner = Callable[[str], str]

GS_PREFIX = "gs://"


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

    credentials, project = google.auth.default()
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
