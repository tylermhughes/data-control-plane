"""Who is making a request, and what they are allowed to do."""

from dataclasses import dataclass

from app.errors import Forbidden


@dataclass(frozen=True)
class Principal:
    key_id: str | None  # None for the server-side CLI
    role: str
    access: str
    project_id: str | None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def can_see_project(self, project_id: str) -> bool:
        return self.is_admin or self.project_id == project_id

    def require_admin(self) -> None:
        if not self.is_admin:
            raise Forbidden("This action needs an admin API key.")

    def require_write(self) -> None:
        if self.access != "write":
            raise Forbidden("This API key is read-only.")


CLI = Principal(key_id=None, role="admin", access="write", project_id=None)
