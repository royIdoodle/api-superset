from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ImageAsset
from ..schemas import StatsResponse


router = APIRouter()


@router.get("", response_model=StatsResponse)
def stats(db: Session = Depends(get_db)) -> StatsResponse:
    total_images = db.query(func.count(ImageAsset.id)).scalar() or 0
    total_size = db.query(func.coalesce(func.sum(ImageAsset.size_bytes), 0)).scalar() or 0

    # 按格式
    fmt_rows = db.query(ImageAsset.format, func.count(ImageAsset.id)).group_by(ImageAsset.format).all()
    by_format = {fmt or "unknown": cnt for fmt, cnt in fmt_rows}

    # 按 bucket
    bkt_rows = db.query(ImageAsset.bucket, func.count(ImageAsset.id)).group_by(ImageAsset.bucket).all()
    by_bucket = {b: cnt for b, cnt in bkt_rows}

    # 最近30天每日上传量
    start_day = (datetime.utcnow().date() - timedelta(days=29))
    day_col = func.date(ImageAsset.created_at)
    day_rows = (
        db.query(day_col.label("day"), func.count(ImageAsset.id))
        .filter(ImageAsset.created_at >= start_day)
        .group_by(day_col)
        .order_by(day_col)
        .all()
    )
    day_map = {str(d): cnt for d, cnt in day_rows}
    uploads_by_day: List[dict] = []
    for i in range(30):
        d = start_day + timedelta(days=i)
        key = str(d)
        uploads_by_day.append({"date": key, "count": int(day_map.get(key, 0))})

    return StatsResponse(
        total_images=int(total_images),
        total_size_bytes=int(total_size),
        by_format={k: int(v) for k, v in by_format.items()},
        by_bucket={k: int(v) for k, v in by_bucket.items()},
        uploads_by_day=uploads_by_day,
    )


