import base64
import importlib.util
from pathlib import Path

from app.services import signing


def test_standard_webhooks_reference_vector() -> None:
    """The example from the Standard Webhooks spec, so off-the-shelf receivers verify us."""
    secret = base64.b64decode("MfKQ9r8GKYqrTwjUPD8ILPZIo2LaLaSw")
    signature = signing.sign(
        secret, "msg_p5jXN8AQM9LWM0D4loKWxJek", 1614265330, b'{"test": 2432232314}'
    )
    assert signature == "v1,g0hM9SsE+OTPJTGt/tmIKtSyZlE3uFJELVlNIOLJ1OE="


def test_derived_secrets_are_stable_and_distinct() -> None:
    a1 = signing.display_secret("whk_a", 1)
    assert a1 == signing.display_secret("whk_a", 1)
    assert a1.startswith("whsec_")
    assert a1 != signing.display_secret("whk_a", 2)
    assert a1 != signing.display_secret("whk_b", 1)


def test_verify_accepts_any_of_several_signatures() -> None:
    old, new = signing.display_secret("whk_a", 1), signing.display_secret("whk_a", 2)
    body = b'{"x":1}'
    header = " ".join(
        signing.sign(signing.endpoint_secret("whk_a", v), "evt_1", 100, body) for v in (2, 1)
    )
    assert signing.verify(new, "evt_1", 100, body, header)
    assert signing.verify(old, "evt_1", 100, body, header)
    assert not signing.verify(signing.display_secret("whk_b", 1), "evt_1", 100, body, header)
    assert not signing.verify(new, "evt_1", 100, b'{"x":2}', header)  # tampered body


def test_receiver_script_agrees_with_signing() -> None:
    path = Path(__file__).parent.parent / "scripts" / "webhook_receiver.py"
    spec = importlib.util.spec_from_file_location("receiver", path)
    assert spec and spec.loader
    receiver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(receiver)

    import time

    now = int(time.time())
    secret = signing.display_secret("whk_a", 1)
    header = signing.sign(signing.endpoint_secret("whk_a", 1), "evt_1", now, b"{}")
    assert receiver.verify(secret, "evt_1", str(now), b"{}", header)
    stale = signing.sign(signing.endpoint_secret("whk_a", 1), "evt_1", now - 3600, b"{}")
    assert not receiver.verify(secret, "evt_1", str(now - 3600), b"{}", stale)
