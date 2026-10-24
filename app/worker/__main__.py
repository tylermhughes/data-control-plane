"""Background worker. Run with: python -m app.worker

Each round it queues new events for webhook endpoints, sends due deliveries, and once an
hour does housekeeping. It keeps going after errors, logging them, so one bad round never
stops delivery for good.
"""

import logging
import signal
import threading
import time

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_engine
from app.services import dispatch

logger = logging.getLogger("app.worker")
HOUSEKEEPING_EVERY = 3600.0


def run_once(session: Session) -> int:
    """One round of work. Returns how many things it did (0 means idle)."""
    done = dispatch.dispatch_events(session)
    done += dispatch.send_due(session)
    return done


def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())

    logger.info("worker started")
    last_housekeeping = 0.0
    while not stop.is_set():
        did_work = False
        try:
            with Session(get_engine(), expire_on_commit=False) as session:
                did_work = run_once(session) > 0
                if time.monotonic() - last_housekeeping > HOUSEKEEPING_EVERY:
                    dispatch.clean_up(session)
                    last_housekeeping = time.monotonic()
        except Exception:
            logger.exception("worker round failed; retrying shortly")
        if not did_work:
            stop.wait(settings.worker_poll_seconds)
    logger.info("worker stopped")


if __name__ == "__main__":
    main()
