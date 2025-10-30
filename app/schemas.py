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


class PdfTransferRequest(BaseModel):
    url: str = Field(..., description="在线PDF文件URL")
    bucket: Optional[str] = Field(None, description="目标 OSS bucket，不填则用默认配置")


class PdfTransferResponse(BaseModel):
    bucket: str
    key: str
    url: Optional[str] = None


