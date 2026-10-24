from enum import StrEnum


class CauseCheckStatus(StrEnum):
    FOUND = "found"
    NOT_APPLICABLE = "not_applicable"
    NOT_CHECKED = "not_checked"
    OK = "ok"

    def __str__(self) -> str:
        return str(self.value)
