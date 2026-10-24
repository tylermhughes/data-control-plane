"""Database tables. Every table module must be imported here so Alembic can see it."""

from app.models.api_key import ApiKey
from app.models.base import Base
from app.models.batch import Batch
from app.models.capability import Capability
from app.models.data_source import DataSource
from app.models.dataset import Dataset, DatasetVersion, EvalResult
from app.models.event import Event
from app.models.idempotency import IdempotencyRecord
from app.models.project import Project
from app.models.request import Allocation, Request
from app.models.spec import Spec, SpecVersion
from app.models.webhook import WebhookDelivery, WebhookEndpoint

__all__ = [
    "Allocation",
    "ApiKey",
    "Base",
    "Batch",
    "Capability",
    "DataSource",
    "Dataset",
    "DatasetVersion",
    "EvalResult",
    "Event",
    "IdempotencyRecord",
    "Project",
    "Request",
    "Spec",
    "SpecVersion",
    "WebhookDelivery",
    "WebhookEndpoint",
]
