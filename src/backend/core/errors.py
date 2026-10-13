"""Stable, credential-free HTTP errors."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_error(_request: Request, error: HTTPException) -> JSONResponse:
        return JSONResponse(
            {"error": {"message": str(error.detail), "fields": {}}},
            status_code=error.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(
        _request: Request, error: RequestValidationError
    ) -> JSONResponse:
        fields = {".".join(map(str, e["loc"][1:])): e["msg"] for e in error.errors()}
        return JSONResponse(
            {"error": {"message": "Check the submitted fields.", "fields": fields}},
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def unexpected_error(_request: Request, error: Exception) -> JSONResponse:
        # Database exceptions can contain connection strings and SQL parameters.
        logger.error("Request failed (%s)", type(error).__name__)
        return JSONResponse(
            {"error": {"message": "Unable to complete the request.", "fields": {}}},
            status_code=500,
        )
