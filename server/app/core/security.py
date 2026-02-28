from datetime import datetime, timedelta, timezone
from typing import Tuple
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import http_error
from app.db.session import get_db
from app.models.device import Device
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(data: dict, settings: Settings) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.jwt_expires_seconds)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Tuple[User, Device]:
    if credentials is None:
        raise http_error(401, "unauthorized", "Missing bearer token")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("user_id")
        device_id = payload.get("device_id")
        device_type = payload.get("device_type")
    except JWTError:
        raise http_error(401, "unauthorized", "Invalid token")

    if not user_id or not device_id:
        raise http_error(401, "unauthorized", "Invalid token payload")

    try:
        user_uuid = UUID(str(user_id))
    except ValueError:
        raise http_error(401, "unauthorized", "Invalid user id in token")

    device = db.query(Device).filter(Device.device_id == device_id).first()
    if device is None or str(device.user_id) != str(user_id):
        raise http_error(403, "forbidden", "Device not paired or user mismatch")

    user = db.get(User, user_uuid)
    if user is None:
        raise http_error(403, "forbidden", "User not found")

    # Optional device_type check to match token
    if device_type and device.device_type != device_type:
        raise http_error(403, "forbidden", "Device type mismatch")

    return user, device
