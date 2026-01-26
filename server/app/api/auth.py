from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import http_error
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.device import Device
from app.schemas.auth import TokenRequest, TokenResponse

router = APIRouter(tags=["Auth"])


@router.post("/auth/token", response_model=TokenResponse)
def issue_token(payload: TokenRequest, db: Session = Depends(get_db)):
    device = (
        db.query(Device)
        .filter(Device.device_id == payload.device_id, Device.device_type == payload.device_type)
        .first()
    )
    if device is None or device.user_id is None:
        raise http_error(status.HTTP_403_FORBIDDEN, "forbidden", "Device not paired")

    settings = get_settings()
    token = create_access_token(
        {"user_id": str(device.user_id), "device_id": device.device_id, "device_type": device.device_type},
        settings,
    )
    return TokenResponse(access_token=token, expires_in=settings.jwt_expires_seconds)
