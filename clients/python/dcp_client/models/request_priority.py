from enum import StrEnum


class RequestPriority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"

    def __str__(self) -> str:
        return str(self.value)
