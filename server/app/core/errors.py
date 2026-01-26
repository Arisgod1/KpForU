from fastapi import HTTPException, status
from app.core.config import ErrorDetail


def http_error(status_code: int, code: str, message: str, details: dict | None = None) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ErrorDetail(code=code, message=message, details=details).model_dump(),
    )
