from enum import StrEnum


class BatchStatus(StrEnum):
    ACCEPTED = "accepted"
    CHECKING = "checking"
    FAILED = "failed"
    PASSED = "passed"
    RECEIVED = "received"
    REJECTED = "rejected"

    def __str__(self) -> str:
        return str(self.value)
