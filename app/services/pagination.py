from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select
from sqlalchemy.orm import InstrumentedAttribute, Session


def paginate[M](
    session: Session,
    stmt: Select[M],
    id_column: InstrumentedAttribute[Any],
    *,
    limit: int,
    cursor: str | None,
) -> tuple[Sequence[M], str | None]:
    """Return one page ordered by ID (IDs sort by creation time) and the cursor for the next."""
    if cursor:
        stmt = stmt.where(id_column > cursor)
    rows = session.scalars(stmt.order_by(id_column).limit(limit + 1)).all()
    if len(rows) > limit:
        rows = rows[:limit]
        return rows, getattr(rows[-1], id_column.key)
    return rows, None
