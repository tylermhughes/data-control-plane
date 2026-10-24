from enum import StrEnum


class RequestStatus(StrEnum):
    CANCELLED = "cancelled"
    CLOSED = "closed"
    DRAFT = "draft"
    OPEN = "open"

    def __str__(self) -> str:
        return str(self.value)
