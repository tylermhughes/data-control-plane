import pytest

from app.services.urls import check_resolved, check_webhook_url


@pytest.mark.parametrize(
    "url",
    [
        "https://hooks.example.com/dcp",
        "http://host.docker.internal:9000/",
        "http://10.0.4.12/internal-tool",
        "http://localhost:9000",
    ],
)
def test_allowed(url: str) -> None:
    check_webhook_url(url)


@pytest.mark.parametrize(
    ("url", "reason"),
    [
        ("ftp://example.com/x", "http:// or https://"),
        ("file:///etc/passwd", "http:// or https://"),
        ("http://169.254.169.254/latest/meta-data/", "metadata"),
        ("http://[fe80::1]/", "metadata"),
        ("http://metadata.google.internal/", "metadata"),
        ("https:///no-host", "no host"),
    ],
)
def test_blocked(url: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        check_webhook_url(url)


def test_hostnames_are_checked_again_when_resolved() -> None:
    check_resolved("http://127.0.0.1:9000/")
    with pytest.raises(ValueError, match="blocked"):
        check_resolved("http://169.254.169.254/")
