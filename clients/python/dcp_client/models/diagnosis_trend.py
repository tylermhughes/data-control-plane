from enum import StrEnum


class DiagnosisTrend(StrEnum):
    FLATTENING = "flattening"
    IMPROVING = "improving"
    NOT_ENOUGH_DATA = "not_enough_data"

    def __str__(self) -> str:
        return str(self.value)
