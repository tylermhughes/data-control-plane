from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, Field, PlainSerializer

# Money travels as a string ("25000.00") so it is never rounded by floating point.
Money = Annotated[
    Decimal,
    Field(ge=0, max_digits=14, decimal_places=4, examples=["25000.00"]),
]


def format_money(value: Decimal) -> str:
    """One canonical form, so scripts and Terraform never see a false change:
    at least 2 decimal places, up to 4 when needed ("25000.00", "30000.50", "0.0125")."""
    value = value.quantize(Decimal("0.0001")).normalize()
    if value.as_tuple().exponent > -2:  # type: ignore[operator]
        value = value.quantize(Decimal("0.01"))
    return f"{value:f}"


MoneyOut = Annotated[
    Decimal, PlainSerializer(format_money, return_type=str), Field(examples=["25000.00"])
]
Currency = Annotated[
    str, Field(pattern=r"^[A-Z]{3}$", description="ISO 4217 code.", examples=["USD"])
]
Description = Field("", max_length=10_000)
ProjectIdIn = Field(
    None,
    description="Project to create this in. Optional for project keys (defaults to their "
    "project); required for admin keys.",
    examples=["prj_01m5n7gwqfa18zhpw1zwh7w2zy"],
)


class Problem(BaseModel):
    """An error, in the RFC 9457 "problem details" format."""

    type: str = Field("about:blank", description="A URI identifying the kind of problem.")
    title: str = Field(description="Short summary of the kind of problem.", examples=["Conflict"])
    status: int = Field(description="HTTP status code.", examples=[409])
    detail: str = Field(
        description="What went wrong, in plain language.",
        examples=["A project named 'Fulfillment vision' already exists."],
    )
    errors: list[dict[str, Any]] | None = Field(
        None, description="For validation problems: one entry per invalid field."
    )


class Page[T](BaseModel):
    data: list[T]
    next_cursor: str | None = Field(
        description="Pass as `cursor` to get the next page. Null on the last page."
    )
