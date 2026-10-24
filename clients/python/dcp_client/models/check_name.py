from enum import StrEnum


class CheckName(StrEnum):
    ACCEPTANCE_RULES = "acceptance_rules"
    ATTRIBUTE_COUNTS = "attribute_counts"
    DUPLICATES = "duplicates"
    FILES = "files"
    FORMAT = "format"
    SCHEMA = "schema"
    STATS = "stats"

    def __str__(self) -> str:
        return str(self.value)
