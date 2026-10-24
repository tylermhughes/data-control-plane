from enum import StrEnum


class ListDeliveriesStatusType0(StrEnum):
    DELIVERED = "delivered"
    FAILED = "failed"
    PENDING = "pending"

    def __str__(self) -> str:
        return str(self.value)
