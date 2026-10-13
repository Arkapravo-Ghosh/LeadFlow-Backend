"""LeadFlow application factory, with an internal readiness endpoint."""

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.core.dependencies import Database
from backend.core.errors import install_error_handlers
from backend.core.security import verify_api_key
from backend.discussions.router import router as discussions_router
from backend.leads.router import router as leads_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="LeadFlow API",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    install_error_handlers(app)
    for router in (leads_router, discussions_router):
        app.include_router(
            router, prefix="/api/v1", dependencies=[Depends(verify_api_key)]
        )

    @app.get("/api/v1/health", include_in_schema=False)
    def health(session: Database) -> JSONResponse:
        try:
            session.execute(text("SELECT 1"))
            return JSONResponse({"status": "ok"})
        except SQLAlchemyError:
            return JSONResponse({"status": "unavailable"}, status_code=503)

    return app


app = create_app()
