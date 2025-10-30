from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, BigInteger, Index
from sqlalchemy.dialects.mysql import JSON as MySQLJSON

from .database import Base


class ImageAsset(Base):
    __tablename__ = "image_assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_filename = Column(String(255), nullable=False)
    bucket = Column(String(128), nullable=False, index=True)
    oss_key = Column(String(512), nullable=False, unique=True)
    url = Column(String(1024), nullable=True)

    size_bytes = Column(BigInteger, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    format = Column(String(16), nullable=False, index=True)

    # 使用 callable 作为默认值，避免可变默认值在进程间共享
    tags = Column(MySQLJSON, nullable=False, default=list)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_image_assets_bucket_format", "bucket", "format"),
    )


