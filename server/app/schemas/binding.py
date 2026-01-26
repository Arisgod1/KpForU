from pydantic import BaseModel, Field


class WatchRegisterRequest(BaseModel):
    device_id: str
    bind_code: str = Field(min_length=4, max_length=32)


class WatchRegisterResponse(BaseModel):
    watch_device_id: str
    bind_code: str
    registered: bool


class PairRequest(BaseModel):
    phone_device_id: str
    bind_code: str


class PairResponse(BaseModel):
    user_id: str
    phone_device_id: str
    watch_device_id: str
    paired: bool
