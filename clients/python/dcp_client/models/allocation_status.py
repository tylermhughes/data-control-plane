from enum import StrEnum


class AllocationStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    COMPLETE = "complete"
    PLANNED = "planned"

    def __str__(self) -> str:
        return str(self.value)
