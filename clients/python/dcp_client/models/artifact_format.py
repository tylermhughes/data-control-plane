from enum import StrEnum


class ArtifactFormat(StrEnum):
    CSV = "csv"
    IMAGES = "images"
    JSONL = "jsonl"
    OTHER = "other"
    PARQUET = "parquet"

    def __str__(self) -> str:
        return str(self.value)
