from pydantic import BaseModel


class WatchWallpaperResponse(BaseModel):
    url: str | None = None


class WatchWallpaperUpdateRequest(BaseModel):
    url: str | None = None
