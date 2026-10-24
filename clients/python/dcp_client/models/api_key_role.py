from enum import StrEnum


class ApiKeyRole(StrEnum):
    ADMIN = "admin"
    PROJECT = "project"

    def __str__(self) -> str:
        return str(self.value)
