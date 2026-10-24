from enum import StrEnum


class BatchDecisionSourceType0(StrEnum):
    DCP = "dcp"
    EXTERNAL = "external"

    def __str__(self) -> str:
        return str(self.value)
