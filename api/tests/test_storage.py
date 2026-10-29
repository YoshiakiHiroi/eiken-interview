import pytest

from eiken_api.services.storage import sign_gs_urls, split_gs_url


def test_split_gs_url() -> None:
    assert split_gs_url("gs://bucket/sets/pre2_0001/q1.mp3") == ("bucket", "sets/pre2_0001/q1.mp3")


@pytest.mark.parametrize("url", ["https://x/y", "gs://bucket", "gs:///obj"])
def test_split_gs_url_rejects_invalid(url: str) -> None:
    with pytest.raises(ValueError):
        split_gs_url(url)


def test_sign_gs_urls_replaces_only_gs_strings_recursively() -> None:
    data = {"a": "gs://b/1", "b": ["gs://b/2", "text", 3], "c": {"d": None, "e": "gs://b/3"}}
    signed = sign_gs_urls(data, lambda url: f"signed:{url}")
    assert signed == {
        "a": "signed:gs://b/1",
        "b": ["signed:gs://b/2", "text", 3],
        "c": {"d": None, "e": "signed:gs://b/3"},
    }
