from typing import Any

from pydantic import BaseModel, Field


class Problem(BaseModel):
    """An error, in the RFC 9457 "problem details" format."""

    type: str = Field("about:blank", description="A URI identifying the kind of problem.")
    title: str = Field(description="Short summary of the kind of problem.")
    status: int = Field(description="HTTP status code.")
    detail: str = Field(description="What went wrong, in plain language.")
    errors: list[dict[str, Any]] | None = Field(
        None, description="For validation problems: one entry per invalid field."
    )


class Page[T](BaseModel):
    data: list[T]
    next_cursor: str | None = Field(
        description="Pass as `cursor` to get the next page. Null on the last page."
    )
