from enum import StrEnum


class AcceptanceRuleOperator(StrEnum):
    VALUE_0 = ">="
    VALUE_1 = ">"
    VALUE_2 = "<="
    VALUE_3 = "<"
    VALUE_4 = "=="

    def __str__(self) -> str:
        return str(self.value)
