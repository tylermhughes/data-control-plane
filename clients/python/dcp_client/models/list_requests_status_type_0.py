from enum import StrEnum


class ListRequestsStatusType0(StrEnum):
    CANCELLED = "cancelled"
    CLOSED = "closed"
    DRAFT = "draft"
    OPEN = "open"

    def __str__(self) -> str:
        return str(self.value)
