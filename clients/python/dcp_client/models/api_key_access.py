from enum import StrEnum


class ApiKeyAccess(StrEnum):
    READ = "read"
    WRITE = "write"

    def __str__(self) -> str:
        return str(self.value)
