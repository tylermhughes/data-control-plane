import pytest

from app.config import get_settings
from app.services import crypto


def test_round_trip_and_ciphertext_hides_the_secret() -> None:
    token = crypto.encrypt({"access_key_id": "AKIA123", "secret_access_key": "s3cr3t"})
    assert "s3cr3t" not in token
    assert crypto.decrypt(token) == {"access_key_id": "AKIA123", "secret_access_key": "s3cr3t"}


def test_changed_master_key_gives_a_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    token = crypto.encrypt({"k": "v"})
    monkeypatch.setattr(get_settings(), "dcp_secret_key", "another-master-key-of-enough-length-000")
    with pytest.raises(ValueError, match="DCP_SECRET_KEY has changed"):
        crypto.decrypt(token)
