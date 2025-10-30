from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ImageOut(BaseModel):
    id: int
    original_filename: str
    bucket: str
    oss_key: str
    url: Optional[str] = None
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None
    format: str
    tags: List[str] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class ImageListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[ImageOut]


class StatsResponse(BaseModel):
    total_images: int
    total_size_bytes: int
    by_format: dict
    by_bucket: dict
    uploads_by_day: List[dict]


