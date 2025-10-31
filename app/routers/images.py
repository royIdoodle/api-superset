import mimetypes
import logging

logger = logging.getLogger(__name__)

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ImageAsset
from ..oss import upload_bytes, suggest_object_key
from ..schemas import ImageListResponse, ImageOut
from ..tinify_client import compress_and_resize, is_enabled as tinify_enabled
from ..config import get_settings


router = APIRouter()


def _normalize_format(fmt: Optional[str]) -> Optional[str]:
    if not fmt:
        return None
    fmt = fmt.lower()
    if fmt == "jpeg":
        fmt = "jpg"
    if fmt not in {"png", "jpg", "webp"}:
        return None
    return fmt


def _infer_format_from_filename(filename: str) -> Optional[str]:
    if "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        return _normalize_format(ext)
    return None


def _content_type_for(fmt: Optional[str]) -> Optional[str]:
    if fmt == "png":
        return "image/png"
    if fmt == "jpg":
        return "image/jpeg"
    if fmt == "webp":
        return "image/webp"
    return None


@router.post("/upload", response_model=ImageOut, status_code=status.HTTP_201_CREATED)
async def upload_image(
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    bucket: Optional[str] = Form(None, description="目标 OSS bucket，不填则用默认配置"),
    tags: Optional[str] = Form(None, description="逗号分隔的标签，如：banner,home"),
    width: Optional[int] = Form(None, description="目标宽度，可选"),
    height: Optional[int] = Form(None, description="目标高度，可选"),
    target_format: Optional[str] = Form(None, description="目标格式：png/jpg/webp，可选"),
):
    # 校验 bucket
    settings = get_settings()
    allowed_buckets = settings.OSS_BUCKETS or []
    default_bucket = settings.DEFAULT_OSS_BUCKET
    final_bucket = bucket

    if bucket:
        if allowed_buckets and bucket not in allowed_buckets:
            if default_bucket:
                final_bucket = default_bucket
            else:
                raise HTTPException(status_code=400, detail=f"不支持的 bucket: {bucket}")
    else:
        if not default_bucket:
            raise HTTPException(status_code=400, detail="未提供 bucket 且未配置默认 bucket")
        final_bucket = default_bucket

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="上传文件为空")

    to_format = _normalize_format(target_format) or _infer_format_from_filename(file.filename)

    out_data = data
    out_width = None
    out_height = None
    out_format = to_format

    if tinify_enabled():
        out_data, out_width, out_height, fmt_from_tiny = compress_and_resize(
            data,
            target_width=width,
            target_height=height,
            target_format=to_format,
        )
        if fmt_from_tiny:
            out_format = fmt_from_tiny

    content_type = _content_type_for(out_format) or (mimetypes.guess_type(file.filename)[0] or "application/octet-stream")

    # 生成对象key
    object_key = suggest_object_key(file.filename, out_format)

    try:
        # 上传到 OSS
        final_bucket, final_key, public_url = upload_bytes(
            out_data,
            original_filename=file.filename,
            bucket_name=final_bucket,
            key=object_key,
            content_type=content_type,
        )
    except Exception as e:
        # 处理所有错误
        error_detail = f"OSS上传失败: {str(e)}"
        logger.error(error_detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        )

    # 保存数据库记录
    record = ImageAsset(
        original_filename=file.filename,
        bucket=final_bucket,
        oss_key=final_key,
        url=public_url,
        size_bytes=len(out_data),
        width=out_width,
        height=out_height,
        # 统一保存为规范化格式（png/jpg/webp），无法识别则为 bin
        format=_normalize_format(out_format or _infer_format_from_filename(file.filename)) or "bin",
        tags=[t.strip() for t in (tags or "").split(",") if t.strip()],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ImageOut.model_validate(record)


@router.get("", response_model=ImageListResponse)
def list_images(
    *,
    db: Session = Depends(get_db),
    bucket: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    fmt: Optional[str] = Query(None, description="图片格式过滤，如 png/jpg/webp"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    q = db.query(ImageAsset)
    if bucket:
        q = q.filter(ImageAsset.bucket == bucket)
    if tag:
        # JSON 数组包含指定标签
        q = q.filter(ImageAsset.tags.contains([tag]))
    if fmt:
        q = q.filter(ImageAsset.format == _normalize_format(fmt) or fmt)

    total = q.count()
    ordering = desc(ImageAsset.created_at) if order == "desc" else asc(ImageAsset.created_at)
    items = q.order_by(ordering).offset((page - 1) * size).limit(size).all()

    return ImageListResponse(total=total, page=page, size=size, items=[ImageOut.model_validate(i) for i in items])


@router.get("/{image_id}", response_model=ImageOut)
def get_image_detail(image_id: int, db: Session = Depends(get_db)) -> ImageOut:
    record = db.get(ImageAsset, image_id)
    if not record:
        raise HTTPException(status_code=404, detail="未找到图片")
    return ImageOut.model_validate(record)


