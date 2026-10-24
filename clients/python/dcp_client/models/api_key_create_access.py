from enum import StrEnum


class ApiKeyCreateAccess(StrEnum):
    READ = "read"
    WRITE = "write"

    def __str__(self) -> str:
        return str(self.value)
