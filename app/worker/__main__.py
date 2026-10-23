"""Background worker. Run with: python -m app.worker

M0 placeholder: it starts, logs a heartbeat, and stops cleanly. Later milestones add
the job queue (quality checks, connectors, webhook delivery) to this loop.
"""

import logging
import signal
import threading

from app.config import get_settings

logger = logging.getLogger("app.worker")


def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())

    logger.info("worker started")
    while not stop.wait(settings.worker_poll_seconds):
        logger.debug("worker idle")
    logger.info("worker stopped")


if __name__ == "__main__":
    main()
