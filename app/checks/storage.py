"""Reading delivered files: local files (file://, inside DCP_LOCAL_DATA_DIR) and S3 (s3://).

Files are streamed, never loaded whole, and their SHA-256 and size are worked out as they're
read. S3 credentials come from the standard AWS settings; DCP_S3_ENDPOINT_URL points boto3 at
S3-compatible storage (Cloudflare R2, Wasabi, ...).
"""

import hashlib
import io
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, BinaryIO
from urllib.parse import unquote, urlsplit

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings


class StorageError(Exception):
    """A file couldn't be read. The message is shown in the check results."""


def _default_s3_client() -> Any:
    return boto3.client("s3", endpoint_url=get_settings().dcp_s3_endpoint_url or None)


# Tests swap this for a stubbed client.
s3_client_factory: Callable[[], Any] = _default_s3_client


class HashingReader(io.RawIOBase):
    """Wraps a stream, keeping a running SHA-256 and byte count of everything read."""

    def __init__(self, raw: Any) -> None:
        self.raw = raw
        self.sha256 = hashlib.sha256()
        self.size = 0

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:
        chunk = self.raw.read(len(buffer))
        if not chunk:
            return 0
        n = len(chunk)
        buffer[:n] = chunk
        self.sha256.update(chunk)
        self.size += n
        return n

    def drain(self) -> None:
        """Read whatever is left, so the checksum and size cover the whole file."""
        while self.readinto(bytearray(1 << 20)):
            pass


@contextmanager
def open_artifact(uri: str) -> Iterator[HashingReader]:
    parts = urlsplit(uri)
    if parts.scheme == "file":
        with _open_local(parts.path) as raw:
            yield HashingReader(raw)
    elif parts.scheme == "s3":
        body = _open_s3(parts.netloc, parts.path.lstrip("/"))
        try:
            yield HashingReader(body)
        finally:
            body.close()
    else:
        raise StorageError(f"Can't read '{parts.scheme}://' files yet (use s3:// or file://).")


@contextmanager
def _open_local(raw_path: str) -> Iterator[BinaryIO]:
    root = Path(get_settings().dcp_local_data_dir).resolve()
    path = Path(unquote(raw_path)).resolve()
    if not path.is_relative_to(root):
        raise StorageError(f"Local files must be inside {root} (got {path}).")
    try:
        with path.open("rb") as handle:
            yield handle
    except FileNotFoundError:
        raise StorageError(f"File not found: {path}") from None
    except OSError as exc:
        raise StorageError(f"Can't read {path}: {exc.strerror}") from None


def _open_s3(bucket: str, key: str) -> Any:
    if not bucket or not key:
        raise StorageError("s3:// URIs need a bucket and a key, e.g. s3://bucket/path/file.jsonl")
    try:
        return s3_client_factory().get_object(Bucket=bucket, Key=key)["Body"]
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in ("NoSuchKey", "404"):
            raise StorageError(f"Not found: s3://{bucket}/{key}") from None
        if code in ("AccessDenied", "403"):
            raise StorageError(f"Access denied: s3://{bucket}/{key}") from None
        if code == "NoSuchBucket":
            raise StorageError(f"No such bucket: {bucket}") from None
        raise StorageError(f"S3 error {code or 'unknown'} for s3://{bucket}/{key}") from None
    except BotoCoreError as exc:  # no credentials, endpoint unreachable, ...
        raise StorageError(f"Can't reach S3: {exc}") from None
