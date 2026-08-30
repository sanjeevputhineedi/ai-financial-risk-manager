import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.core.database import Base, engine, check_database_health
from backend.app.core.middleware import RequestContextMiddleware
from backend.app.core.errors import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler
)
from backend.app.api.v1.api import api_router

# Configure structured logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    # Initialize DB tables if needed
    Base.metadata.create_all(bind=engine)
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Simulated UPI-like payment protection system using multi-layer AI risk assessment and cooling period escrow.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Custom Middlewares
app.add_middleware(RequestContextMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/health", tags=["Health"])
def health_check():
    """
    Checkpoint M1 Acceptance:
    Returns system status, database connection state, environment, and timestamp.
    """
    db_healthy = check_database_health()
    return {
        "status": "healthy" if db_healthy else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Mount API version 1
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount Frontend static files & single page application
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", tags=["Frontend"])
    async def serve_frontend():
        index_path = os.path.join(frontend_dir, "index.html")
        return FileResponse(index_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

