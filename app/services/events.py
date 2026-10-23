from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ids import new_id
from app.models import Event
from app.services.principal import Principal


def emit(
    session: Session,
    type: str,
    subject: BaseModel,
    *,
    subject_id: str,
    project_id: str | None,
    actor: Principal,
    extra: dict[str, Any] | None = None,
) -> None:
    """Record an event in the caller's transaction, so it is saved if and only if the change is.

    `data` is the subject as the API shows it, plus any `extra` context (e.g. `changes`).
    """
    data: dict[str, Any] = {**subject.model_dump(mode="json"), **(extra or {})}
    session.add(
        Event(
            id=new_id("evt"),
            type=type,
            subject_id=subject_id,
            project_id=project_id,
            actor_key_id=actor.key_id,
            data=data,
        )
    )
