import uuid
from typing import Optional, Tuple
from urllib.parse import urlparse

import oss2

from .config import get_settings


settings = get_settings()

_auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)


def get_bucket(bucket_name: Optional[str] = None) -> oss2.Bucket:
    name = bucket_name or settings.DEFAULT_OSS_BUCKET
    if not name:
        raise ValueError("未配置 DEFAULT_OSS_BUCKET，且未提供 bucket 名称")
    return oss2.Bucket(_auth, settings.OSS_ENDPOINT, name)


def build_public_url(bucket_name: str, key: str) -> Optional[str]:
    """根据 endpoint 推断公有读URL（要求 bucket 配置为公有读）。
    若 endpoint 不是 http(s) 形式，则返回 None。
    """
    parsed = urlparse(settings.OSS_ENDPOINT)
    if parsed.scheme and parsed.netloc:
        host = parsed.netloc
        return f"{parsed.scheme}://{bucket_name}.{host}/{key}"
    return None


def suggest_object_key(original_filename: str, target_ext: Optional[str] = None) -> str:
    suffix = (target_ext or "").lower().lstrip(".")
    if not suffix and "." in original_filename:
        suffix = original_filename.rsplit(".", 1)[-1].lower()
    uid = uuid.uuid4().hex
    return f"uploads/{uid}.{suffix or 'bin'}"


def upload_bytes(
    data: bytes,
    *,
    original_filename: str,
    bucket_name: Optional[str] = None,
    key: Optional[str] = None,
    content_type: Optional[str] = None,
) -> Tuple[str, str, Optional[str]]:
    """上传字节到OSS，返回 (bucket, key, public_url)。"""
    bucket = get_bucket(bucket_name)
    object_key = key or suggest_object_key(original_filename)
    headers = {}
    if content_type:
        headers["Content-Type"] = content_type
    bucket.put_object(object_key, data, headers=headers)
    public_url = build_public_url(bucket.bucket_name, object_key)
    return bucket.bucket_name, object_key, public_url


