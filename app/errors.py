"""Errors raised by services and API code. Each becomes an RFC 9457 problem response."""


class DcpError(Exception):
    status = 500
    title = "Internal error"

    def __init__(self, detail: str, headers: dict[str, str] | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.headers = headers


class Unauthorized(DcpError):
    status = 401
    title = "Unauthorized"

    def __init__(self, detail: str) -> None:
        super().__init__(detail, headers={"WWW-Authenticate": "Bearer"})


class Forbidden(DcpError):
    status = 403
    title = "Forbidden"


class NotFound(DcpError):
    status = 404
    title = "Not found"


class Conflict(DcpError):
    status = 409
    title = "Conflict"


class Invalid(DcpError):
    status = 422
    title = "Invalid request"
