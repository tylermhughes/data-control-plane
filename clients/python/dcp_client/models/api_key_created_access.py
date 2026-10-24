from enum import StrEnum


class ApiKeyCreatedAccess(StrEnum):
    READ = "read"
    WRITE = "write"

    def __str__(self) -> str:
        return str(self.value)
