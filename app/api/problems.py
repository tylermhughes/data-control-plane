"""Turns every error into an RFC 9457 problem response (application/problem+json)."""

import functools
import re
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, IntegrityError
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

    @app.exception_handler(DataError)
    async def data_error(_: Request, exc: DataError) -> JSONResponse:
        # The database refused a value (e.g. a NUL character in text, or a number too large).
        detail = "A value in the request can't be stored."
        if "NUL" in str(exc.orig):
            detail = "Text in the request contains a NUL (zero) character, which isn't allowed."
        return problem_response(422, "Invalid request", detail)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        headers = dict(exc.headers or {})
        if exc.status_code == 400 and exc.detail == "There was an error parsing the body":
            # Unreadable bodies (e.g. not UTF-8) are bad input like any other: one status, 422.
            return problem_response(
                422, "Invalid request", "The request body isn't valid JSON text."
            )
        if exc.status_code == 405:
            # Several handlers can share a path; list every method the path supports.
            headers["Allow"] = ", ".join(_allowed_methods(app, request.url.path))
        return problem_response(exc.status_code, str(exc.detail), str(exc.detail), headers=headers)


@functools.cache
def _path_patterns(app: FastAPI) -> list[tuple[re.Pattern[str], frozenset[str]]]:
    patterns = []
    for template, operations in app.openapi()["paths"].items():
        regex = "^" + re.sub(r"\\{[^/]+\\}", "[^/]+", re.escape(template)) + "$"
        patterns.append((re.compile(regex), frozenset(m.upper() for m in operations)))
    return patterns


def _allowed_methods(app: FastAPI, path: str) -> list[str]:
    methods: set[str] = set()
    for pattern, allowed in _path_patterns(app):
        if pattern.match(path):
            methods |= allowed
    return sorted(methods)
