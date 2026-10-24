from enum import StrEnum


class CheckOutcome(StrEnum):
    FAILED = "failed"
    PASSED = "passed"
    SKIPPED = "skipped"
    WARNING = "warning"

    def __str__(self) -> str:
        return str(self.value)
