"""Database tables. Every table module must be imported here so Alembic can see it."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
