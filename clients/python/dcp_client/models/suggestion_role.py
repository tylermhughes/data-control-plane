from enum import StrEnum


class SuggestionRole(StrEnum):
    PILOT = "pilot"
    PROVEN = "proven"

    def __str__(self) -> str:
        return str(self.value)
