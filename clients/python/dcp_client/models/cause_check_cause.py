from enum import StrEnum


class CauseCheckCause(StrEnum):
    DATA_MIX = "data_mix"
    EVAL = "eval"
    LABEL_QUALITY = "label_quality"
    MODEL = "model"
    SATURATION = "saturation"

    def __str__(self) -> str:
        return str(self.value)
