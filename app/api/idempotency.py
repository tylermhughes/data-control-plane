"""Idempotency-Key support for POST requests.

A client that sends the same Idempotency-Key twice gets the first response back instead of a
second resource, so retries (from CI, scripts, Terraform) are always safe.
"""

import hashlib
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import PrincipalDep, SessionDep
from app.errors import Invalid
from app.models import IdempotencyRecord


@dataclass
class Idempotency:
    key: str | None
    api_key_id: str | None
    request_hash: str
    replay: JSONResponse | None = None

    def save(self, session: Session, status_code: int, body: BaseModel) -> None:
        """Remember the response (in the caller's transaction) for future retries."""
        if self.key is None or self.api_key_id is None:
            return
        session.add(
            IdempotencyRecord(
                api_key_id=self.api_key_id,
                key=self.key,
                request_hash=self.request_hash,
                status_code=status_code,
                response_body=jsonable_encoder(body),
            )
        )


async def _idempotency(
    request: Request,
    session: SessionDep,
    principal: PrincipalDep,
    idempotency_key: Annotated[
        str | None,
        Header(
            max_length=255,
            description="Any unique string (e.g. a UUID). Retrying with the same key "
            "returns the original response instead of creating a duplicate.",
        ),
    ] = None,
) -> Idempotency:
    body = await request.body()
    request_hash = hashlib.sha256(
        request.method.encode() + b" " + request.url.path.encode() + b"\n" + body
    ).hexdigest()
    idem = Idempotency(idempotency_key, principal.key_id, request_hash)
    if idempotency_key is None or principal.key_id is None:
        return idem
    record = session.get(IdempotencyRecord, (principal.key_id, idempotency_key))
    if record is None:
        return idem
    if record.request_hash != request_hash:
        raise Invalid("This Idempotency-Key was already used with a different request.")
    idem.replay = JSONResponse(
        record.response_body,
        status_code=record.status_code,
        headers={"Idempotent-Replayed": "true"},
    )
    return idem


IdempotencyDep = Annotated[Idempotency, Depends(_idempotency)]
