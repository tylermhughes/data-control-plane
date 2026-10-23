"""Database tables. Every table module must be imported here so Alembic can see it."""

from app.models.api_key import ApiKey
from app.models.base import Base
from app.models.capability import Capability
from app.models.data_source import DataSource
from app.models.event import Event
from app.models.idempotency import IdempotencyRecord
from app.models.project import Project
from app.models.request import Allocation, Request
from app.models.spec import Spec, SpecVersion

__all__ = [
    "Allocation",
    "ApiKey",
    "Base",
    "Capability",
    "DataSource",
    "Event",
    "IdempotencyRecord",
    "Project",
    "Request",
    "Spec",
    "SpecVersion",
]
