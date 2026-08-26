"""Map domain exceptions → HTTP responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import FaceAuthError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(FaceAuthError)
    async def handle_face_auth_error(request: Request, exc: FaceAuthError):
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "success": False,
                "status_code": exc.http_status,
                "code": getattr(exc, "code", "face_auth_error"),
                "message": exc.message,
            },
        )
