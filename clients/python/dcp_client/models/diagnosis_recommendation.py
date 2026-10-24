from enum import StrEnum


class DiagnosisRecommendation(StrEnum):
    INVESTIGATE = "investigate"
    KEEP_GOING = "keep_going"
    NOT_ENOUGH_DATA = "not_enough_data"
    REFINE_SPEC = "refine_spec"

    def __str__(self) -> str:
        return str(self.value)
