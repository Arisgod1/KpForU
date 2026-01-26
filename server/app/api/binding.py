from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.errors import http_error
from app.db.session import get_db
from app.models.device import Device
from app.models.user import User
from app.schemas.binding import (
    PairRequest,
    PairResponse,
    WatchRegisterRequest,
    WatchRegisterResponse,
)

router = APIRouter(tags=["Binding"])


@router.post("/devices/watch/register", response_model=WatchRegisterResponse, status_code=status.HTTP_201_CREATED)
def watch_register(payload: WatchRegisterRequest, db: Session = Depends(get_db)):
    existing_bind = (
        db.query(Device).filter(Device.bind_code == payload.bind_code, Device.device_id != payload.device_id).first()
    )
    if existing_bind:
        raise http_error(status.HTTP_409_CONFLICT, "conflict", "Bind code already used")

    device = db.query(Device).filter(Device.device_id == payload.device_id).first()
    registered = False
    if device:
        device.bind_code = payload.bind_code
        device.device_type = "watch"
    else:
        registered = True
        device = Device(device_id=payload.device_id, bind_code=payload.bind_code, device_type="watch")
        db.add(device)

    db.commit()
    db.refresh(device)
    return WatchRegisterResponse(watch_device_id=device.device_id, bind_code=device.bind_code, registered=registered)


@router.post("/binding/pair", response_model=PairResponse)
def pair_devices(payload: PairRequest, db: Session = Depends(get_db)):
    watch = db.query(Device).filter(Device.bind_code == payload.bind_code, Device.device_type == "watch").first()
    if watch is None:
        raise http_error(status.HTTP_404_NOT_FOUND, "not_found", "Bind code not found")

    user = watch.user
    if user is None:
        user = User()
        db.add(user)
        db.flush()
        watch.user_id = user.id

    phone = db.query(Device).filter(Device.device_id == payload.phone_device_id).first()
    if phone is None:
        phone = Device(device_id=payload.phone_device_id, device_type="phone", user_id=user.id)
        db.add(phone)
    else:
        phone.device_type = "phone"
        phone.user_id = user.id

    db.commit()
    db.refresh(watch)
    db.refresh(phone)

    return PairResponse(
        user_id=str(user.id),
        phone_device_id=phone.device_id,
        watch_device_id=watch.device_id,
        paired=True,
    )
