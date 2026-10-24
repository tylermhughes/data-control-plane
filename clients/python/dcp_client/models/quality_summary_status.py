from enum import StrEnum


class QualitySummaryStatus(StrEnum):
    ERROR = "error"
    FAILED = "failed"
    PASSED = "passed"
    QUEUED = "queued"
    RUNNING = "running"

    def __str__(self) -> str:
        return str(self.value)
