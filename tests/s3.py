"""The test profile's S3-compatible server (Versity Gateway), started by scripts/check.sh."""

import os
import uuid
from typing import Any

import boto3

ENDPOINT = os.environ.get("TEST_S3_ENDPOINT_URL", "http://127.0.0.1:57070")
ACCESS_KEY, SECRET_KEY = "test-access", "test-secret-key"


def client() -> Any:
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name="us-east-1",
    )


def new_bucket() -> str:
    name = f"t-{uuid.uuid4().hex[:12]}"
    client().create_bucket(Bucket=name)
    return name


def put(bucket: str, key: str, body: bytes) -> None:
    client().put_object(Bucket=bucket, Key=key, Body=body)
