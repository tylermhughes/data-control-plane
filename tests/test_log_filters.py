import logging

from app.log_filters import SkipSuccessfulHealthChecks


def access_record(path: str, status: int) -> logging.LogRecord:
    return logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        __file__,
        1,
        '%s - "%s %s HTTP/%s" %d',
        ("172.18.0.1:5000", "GET", path, "1.1", status),
        None,
    )


def test_successful_health_checks_are_hidden() -> None:
    f = SkipSuccessfulHealthChecks()
    assert not f.filter(access_record("/healthz", 200))
    assert not f.filter(access_record("/readyz", 200))


def test_failed_health_checks_and_real_requests_are_kept() -> None:
    f = SkipSuccessfulHealthChecks()
    assert f.filter(access_record("/readyz", 503))
    assert f.filter(access_record("/v1/projects", 200))
    assert f.filter(access_record("/v1/projects?limit=5", 200))
