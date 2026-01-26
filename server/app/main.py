import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

from app.api import router as api_router
from app.core.config import get_settings
from app.db.session import engine
from app.models import Base

settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")
app.include_router(api_router, prefix="/v1")


@app.on_event("startup")
def on_startup() -> None:
    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    # Auto-create tables for local/dev convenience (migrations recommended in prod)
    Base.metadata.create_all(bind=engine)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if not isinstance(detail, dict):
        detail = {"code": "error", "message": str(detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": str(exc)}},
    )
