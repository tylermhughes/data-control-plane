"""Turns every error into an RFC 9457 problem response (application/problem+json)."""

from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException

from app.errors import DcpError
from app.schemas.common import Problem

PROBLEM_JSON = "application/problem+json"


def problem_response(
    status: int,
    title: str,
    detail: str,
    *,
    errors: list[dict[str, Any]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = Problem(title=title, status=status, detail=detail, errors=errors)
    return JSONResponse(
        jsonable_encoder(body, exclude_none=True),
        status_code=status,
        media_type=PROBLEM_JSON,
        headers=headers,
    )


def problem_responses(*statuses: int) -> dict[int | str, dict[str, Any]]:
    return {s: {"model": Problem, "content": {PROBLEM_JSON: {}}} for s in statuses}


# Error responses to declare on routes, so they appear in the OpenAPI spec.
AUTH_ERRORS = problem_responses(401, 403)
READ_ERRORS = problem_responses(401, 403, 404, 422)
WRITE_ERRORS = problem_responses(401, 403, 404, 409, 422)


def install(app: FastAPI) -> None:
    @app.exception_handler(DcpError)
    async def dcp_error(_: Request, exc: DcpError) -> JSONResponse:
        return problem_response(exc.status, exc.title, exc.detail, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in exc.errors()
        ]
        return problem_response(
            422, "Invalid request", "Some fields are missing or invalid.", errors=errors
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error(_: Request, __: IntegrityError) -> JSONResponse:
        return problem_response(
            409, "Conflict", "The request conflicts with existing data. Please retry."
        )

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
        return problem_response(
            exc.status_code, str(exc.detail), str(exc.detail), headers=exc.headers
        )
