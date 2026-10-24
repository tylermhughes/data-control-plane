"""A tiny webhook receiver for local testing. Built-in Python only; nothing to install.

    python3 scripts/webhook_receiver.py --secret whsec_...            # accept everything
    python3 scripts/webhook_receiver.py --secret whsec_... --fail     # answer 503 (test retries)

Register http://host.docker.internal:9000/ as the endpoint URL: that's how DCP, running
in Docker, reaches this script on your Mac. Every message is printed with whether its
signature checks out. Also a reference for writing a real receiver: see verify().
"""

import argparse
import base64
import hashlib
import hmac
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOLERANCE_SECONDS = 5 * 60  # reject messages older than this (replay protection)


def verify(secret: str, msg_id: str, timestamp: str, body: bytes, signature_header: str) -> bool:
    key = base64.b64decode(secret.removeprefix("whsec_"))
    signed = f"{msg_id}.{timestamp}.".encode() + body
    expected = "v1," + base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()
    fresh = abs(time.time() - int(timestamp)) <= TOLERANCE_SECONDS
    return fresh and any(hmac.compare_digest(expected, s) for s in signature_header.split())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--secret", required=True, help="The endpoint's whsec_... secret")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--fail", action="store_true", help="Answer 503 to every message")
    args = parser.parse_args()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 (name required by http.server)
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            ok = verify(
                args.secret,
                self.headers.get("webhook-id", ""),
                self.headers.get("webhook-timestamp", "0"),
                body,
                self.headers.get("webhook-signature", ""),
            )
            message = json.loads(body or b"{}")
            status = 503 if args.fail else (200 if ok else 401)
            print(
                f"{time.strftime('%H:%M:%S')}  {message.get('type', '?'):<28} "
                f"subject={message.get('subject_id')}  "
                f"signature={'OK' if ok else 'INVALID'}  -> answered {status}",
                flush=True,
            )
            self.send_response(status)
            self.end_headers()
            self.wfile.write(b"ok" if status == 200 else b"no")

        def log_message(self, *_: object) -> None:  # keep the output to one line per message
            pass

    print(f"Listening on http://localhost:{args.port}/  (Ctrl+C to stop)", flush=True)
    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()  # noqa: S104


if __name__ == "__main__":
    main()
