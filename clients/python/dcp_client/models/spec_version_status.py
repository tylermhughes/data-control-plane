from enum import StrEnum


class SpecVersionStatus(StrEnum):
    APPROVED = "approved"
    DRAFT = "draft"

    def __str__(self) -> str:
        return str(self.value)
