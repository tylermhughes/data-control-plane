"""A real HTTP receiver for tests: records each request, answers with a chosen status."""

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


@dataclass
class Received:
    headers: dict[str, str]
    body: bytes

    @property
    def json(self) -> Any:
        return json.loads(self.body)


@dataclass
class Receiver:
    url: str
    status: int = 200
    redirect_to: str | None = None
    received: list[Received] = field(default_factory=list)


@contextmanager
def running_receiver() -> Iterator[Receiver]:
    state = Receiver(url="")

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            state.received.append(Received({k.lower(): v for k, v in self.headers.items()}, body))
            if state.redirect_to:
                self.send_response(302)
                self.send_header("Location", state.redirect_to)
            else:
                self.send_response(state.status)
            self.end_headers()
            self.wfile.write(b"thanks")

        def log_message(self, *_: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    state.url = f"http://127.0.0.1:{server.server_address[1]}/hook"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
