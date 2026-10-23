"""Keep routine health checks out of the access log, so it shows only real activity."""

import logging

HEALTH_PATHS = frozenset({"/healthz", "/readyz"})


class SkipSuccessfulHealthChecks(logging.Filter):
    """Drops successful /healthz and /readyz lines. Failed checks are still logged."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Uvicorn access records carry (client, method, path, http_version, status).
        args = record.args
        if isinstance(args, tuple) and len(args) == 5:
            path, status = str(args[2]).split("?", 1)[0], args[4]
            if path in HEALTH_PATHS and status == 200:
                return False
        return True


def install() -> None:
    logging.getLogger("uvicorn.access").addFilter(SkipSuccessfulHealthChecks())
