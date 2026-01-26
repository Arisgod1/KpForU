from pydantic import BaseModel


class TokenRequest(BaseModel):
    device_id: str
    device_type: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
