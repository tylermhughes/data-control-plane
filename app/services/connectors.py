"""Connectors: watch a bucket folder and turn each new file into a batch.

The worker polls each enabled connector about every `poll_interval_seconds`, lists the files
under its prefix, and creates one batch per new file (external_ref "s3:<key>"), with
delivered_count and spend filled in by DCP after the automatic checks. Files it has seen are
remembered, so nothing is picked up twice; a file that changes (size, date or ETag) is checked
again if its batch is still undecided. Errors are recorded on the connector and retried at the
next poll.
"""

import logging
from collections.abc import Sequence
from datetime import datetime, timedelta
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import urlsplit

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import Conflict, DcpError, Invalid
from app.ids import new_id
from app.models import Allocation, Batch, Connector, ConnectorObject, DataSource
from app.models.base import utcnow
from app.schemas import batches as batch_schemas
from app.schemas import intake as schemas
from app.services import allocations, crypto, events, scoped
from app.services.pagination import paginate
from app.services.principal import Principal

logger = logging.getLogger(__name__)

FORMATS = {".jsonl": "jsonl", ".ndjson": "jsonl", ".csv": "csv", ".parquet": "parquet"}
MAX_NEW_FILES_PER_POLL = 100


def _emit(session: Session, type: str, cnx: Connector, actor: Principal) -> None:
    events.emit(
        session,
        type,
        schemas.Connector.model_validate(cnx),
        subject_id=cnx.id,
        project_id=cnx.project_id,
        actor=actor,
    )


# --- S3 access -------------------------------------------------------------------------------


def s3_client(cnx: Connector) -> Any:
    """A client with the connector's own endpoint and keys (or DCP's defaults)."""
    kwargs: dict[str, Any] = {
        "endpoint_url": cnx.endpoint_url or get_settings().dcp_s3_endpoint_url or None,
        "region_name": cnx.region or None,
        "config": Config(retries={"max_attempts": 3}, connect_timeout=10, read_timeout=60),
    }
    if cnx.credentials_encrypted:
        creds = crypto.decrypt(cnx.credentials_encrypted)
        kwargs.update(
            aws_access_key_id=creds["access_key_id"],
            aws_secret_access_key=creds["secret_access_key"],
            aws_session_token=creds.get("session_token"),
        )
    return boto3.client("s3", **kwargs)


def s3_clients_for(session: Session, batch: Batch) -> dict[str, Any]:
    """Bucket -> client, for the buckets this batch's source has connectors on."""
    buckets = {urlsplit(a["uri"]).netloc for a in batch.artifacts if a["uri"].startswith("s3://")}
    if not buckets:
        return {}
    found = session.scalars(
        select(Connector).where(
            Connector.data_source_id == batch.data_source_id, Connector.bucket.in_(buckets)
        )
    ).all()
    return {cnx.bucket: s3_client(cnx) for cnx in found}


# --- managing connectors ---------------------------------------------------------------------


def list_connectors(
    session: Session,
    actor: Principal,
    *,
    project_id: str | None,
    data_source_id: str | None,
    limit: int,
    cursor: str | None,
) -> tuple[Sequence[Connector], str | None]:
    where = [Connector.data_source_id == data_source_id] if data_source_id else []
    return scoped.list_scoped(
        session, actor, Connector, project_id=project_id, limit=limit, cursor=cursor, where=where
    )


def get_connector(session: Session, actor: Principal, connector_id: str) -> Connector:
    return scoped.get_scoped(session, actor, Connector, connector_id, "connector")


def _check_allocation(session: Session, cnx: Connector, allocation_id: str | None) -> None:
    if allocation_id is None:
        return
    alloc = session.get(Allocation, allocation_id)
    if alloc is None or alloc.data_source_id != cnx.data_source_id:
        raise Invalid("allocation_id must be an allocation of the connector's data source.")


def _set_credentials(cnx: Connector, creds: schemas.S3Credentials | None) -> None:
    if creds is None:
        cnx.credentials_encrypted, cnx.access_key_hint = None, None
    else:
        cnx.credentials_encrypted = crypto.encrypt(creds.model_dump())
        cnx.access_key_hint = "…" + creds.access_key_id[-4:]


def create_connector(
    session: Session, actor: Principal, body: schemas.ConnectorCreate
) -> Connector:
    actor.require_write()
    source = session.get(DataSource, body.data_source_id)
    if source is None or not actor.can_see_project(source.project_id):
        raise Invalid(f"No data source with id '{body.data_source_id}'.")
    cnx = Connector(
        id=new_id("cnx"),
        project_id=source.project_id,
        data_source_id=source.id,
        **body.model_dump(exclude={"data_source_id", "credentials"}),
        next_poll_at=utcnow(),
    )
    _check_allocation(session, cnx, body.allocation_id)
    _set_credentials(cnx, body.credentials)
    session.add(cnx)
    session.flush()
    _emit(session, "connector.created", cnx, actor)
    return cnx


def update_connector(
    session: Session, actor: Principal, connector_id: str, body: schemas.ConnectorUpdate
) -> Connector:
    cnx = get_connector(session, actor, connector_id)
    actor.require_write()
    changes = body.model_dump(exclude_unset=True, exclude={"credentials"})
    nullable = {"endpoint_url", "region", "allocation_id"}
    changes = {k: v for k, v in changes.items() if v is not None or k in nullable}
    if "allocation_id" in changes:
        _check_allocation(session, cnx, changes["allocation_id"])
    scoped.apply_changes(cnx, changes)
    if "credentials" in body.model_fields_set:
        _set_credentials(cnx, body.credentials)
    session.flush()
    _emit(session, "connector.updated", cnx, actor)
    return cnx


def delete_connector(session: Session, actor: Principal, connector_id: str) -> None:
    """Batches it created stay; only the connector and its list of seen files go."""
    cnx = get_connector(session, actor, connector_id)
    actor.require_write()
    _emit(session, "connector.deleted", cnx, actor)
    session.delete(cnx)
    session.flush()


def list_objects(
    session: Session, actor: Principal, connector_id: str, *, limit: int, cursor: str | None
) -> tuple[Sequence[ConnectorObject], str | None]:
    get_connector(session, actor, connector_id)
    stmt = select(ConnectorObject).where(ConnectorObject.connector_id == connector_id)
    return paginate(session, stmt, ConnectorObject.key, limit=limit, cursor=cursor)


# --- polling ---------------------------------------------------------------------------------


def _list_files(client: Any, cnx: Connector) -> list[dict[str, Any]]:
    files = []
    for page in client.get_paginator("list_objects_v2").paginate(
        Bucket=cnx.bucket, Prefix=cnx.prefix
    ):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            name = PurePosixPath(key).name
            if key.endswith("/") or name.startswith((".", "_")):
                continue  # folders, hidden files, _manifest.json and the like
            if PurePosixPath(name).suffix.lower() not in FORMATS:
                continue
            files.append(
                {
                    "key": key,
                    "etag": (obj.get("ETag") or "").strip('"'),
                    "size_bytes": int(obj["Size"]),
                    "last_modified": obj["LastModified"],
                }
            )
    return files


def _describe(exc: Exception, cnx: Connector) -> str:
    where = f"s3://{cnx.bucket}/{cnx.prefix}"
    if isinstance(exc, ClientError):
        code = exc.response.get("Error", {}).get("Code", "unknown")
        if code in ("AccessDenied", "403", "InvalidAccessKeyId", "SignatureDoesNotMatch"):
            return f"Access denied listing {where} ({code}). Check the connector's credentials."
        if code == "NoSuchBucket":
            return f"No such bucket: {cnx.bucket}"
        return f"S3 error {code} listing {where}"
    if isinstance(exc, (BotoCoreError, ValueError)):
        return f"Can't reach the bucket: {exc}"
    return f"{exc.__class__.__name__}: {exc}"


def poll(session: Session, cnx: Connector, *, now: datetime | None = None) -> schemas.PollResult:
    """List the bucket once and turn new files into batches. Commits as it goes."""
    from app.services import batches, quality  # import here: batches imports this module

    now = now or utcnow()
    result = schemas.PollResult(
        connector_id=cnx.id, files_listed=0, new_batches=[], updated_files=[], errors=[]
    )
    cnx.last_polled_at = now
    cnx.next_poll_at = now + timedelta(seconds=cnx.poll_interval_seconds)
    try:
        files = _list_files(s3_client(cnx), cnx)
    except Exception as exc:  # recorded on the connector and retried next poll
        cnx.last_error = _describe(exc, cnx)
        result.errors.append(cnx.last_error)
        session.commit()
        return result
    result.files_listed = len(files)
    seen = {
        o.key: o
        for o in session.scalars(
            select(ConnectorObject).where(ConnectorObject.connector_id == cnx.id)
        )
    }
    actor = Principal(key_id=None, role="project", access="write", project_id=cnx.project_id)
    errors: list[str] = []

    for f in files:
        known = seen.get(f["key"])
        if known is not None:
            if known.batch_id and not known.same_version(f):
                known.etag, known.size_bytes, known.last_modified = (
                    f["etag"],
                    f["size_bytes"],
                    f["last_modified"],
                )
                batch = session.get(Batch, known.batch_id)
                if batch is not None and batch.status in ("received", "passed", "failed"):
                    quality.queue_checks(session, batch, trigger="auto")
                result.updated_files.append(f["key"])
                session.commit()
            continue
        if len(result.new_batches) >= MAX_NEW_FILES_PER_POLL:
            break  # the rest next time
        record = ConnectorObject(connector_id=cnx.id, **f)
        try:
            body = batch_schemas.BatchCreate(
                allocation_id=cnx.allocation_id
                or allocations.single_active(session, cnx.data_source_id),
                artifacts=[
                    batch_schemas.Artifact(
                        uri=f"s3://{cnx.bucket}/{f['key']}",
                        format=FORMATS[PurePosixPath(f["key"]).suffix.lower()],
                        size_bytes=f["size_bytes"],
                    )
                ],
                external_ref=f"s3:{f['key']}"[:200],
                notes=f"Found by connector {cnx.id} in s3://{cnx.bucket}/{f['key']}",
            )
            batch, _ = batches.create_batch(session, actor, body)
            record.batch_id = batch.id
            result.new_batches.append(batch.id)
        except DcpError as exc:  # e.g. no active allocation: keep the file, try again later
            session.rollback()
            errors.append(f"{f['key']}: {exc.detail}")
            continue
        session.add(record)
        cnx = session.get_one(Connector, cnx.id)
        cnx.last_found_at = now
        session.commit()

    cnx = session.get_one(Connector, cnx.id)
    summary = errors[0] if errors else None
    if summary and len(errors) > 1:
        summary += f" (and {len(errors) - 1} more)"
    cnx.last_error = summary
    result.errors = errors
    session.commit()
    return result


def poll_now(session: Session, actor: Principal, connector_id: str) -> schemas.PollResult:
    cnx = get_connector(session, actor, connector_id)
    actor.require_write()
    if not cnx.enabled:
        raise Conflict("This connector is disabled. Enable it first.")
    return poll(session, cnx)


def poll_due(session: Session, *, now: datetime | None = None) -> int:
    """Worker: poll every enabled connector whose time has come. Returns how many polled."""
    now = now or utcnow()
    due = session.scalars(
        select(Connector)
        .where(Connector.enabled.is_(True), Connector.next_poll_at <= now)
        .order_by(Connector.next_poll_at)
        .limit(10)
        .with_for_update(skip_locked=True)
    ).all()
    if not due:
        session.commit()
        return 0
    for cnx in due:  # claim them all first, so another worker skips them
        cnx.next_poll_at = now + timedelta(seconds=cnx.poll_interval_seconds)
    ids = [c.id for c in due]
    session.commit()
    for connector_id in ids:
        try:
            poll(session, session.get_one(Connector, connector_id), now=now)
        except Exception:
            session.rollback()
            logger.exception("polling connector %s failed; will retry", connector_id)
    return len(ids)
