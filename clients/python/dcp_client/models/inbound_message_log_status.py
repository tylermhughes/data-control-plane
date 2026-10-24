from enum import StrEnum


class InboundMessageLogStatus(StrEnum):
    PROCESSED = "processed"
    REJECTED = "rejected"

    def __str__(self) -> str:
        return str(self.value)
