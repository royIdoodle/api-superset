from typing import Optional, Tuple

import tinify

from .config import get_settings


settings = get_settings()

if settings.TINIFY_API_KEY:
    tinify.key = settings.TINIFY_API_KEY


def is_enabled() -> bool:
    return bool(settings.TINIFY_API_KEY)


def compress_and_resize(
    data: bytes,
    *,
    target_width: Optional[int] = None,
    target_height: Optional[int] = None,
    target_format: Optional[str] = None,
) -> Tuple[bytes, Optional[int], Optional[int], Optional[str]]:
    """用 TinyPNG 压缩，支持可选缩放与格式转换。
    返回 (输出字节, 宽, 高, 格式)。宽高在未能获取时返回 None。
    """
    if not is_enabled():
        return data, None, None, None

    source = tinify.from_buffer(data)

    # 尺寸调整
    if target_width and target_height:
        source = source.resize(method="fit", width=target_width, height=target_height)
    elif target_width and not target_height:
        source = source.resize(method="scale", width=target_width)
    elif target_height and not target_width:
        source = source.resize(method="scale", height=target_height)

    # 格式转换（支持 png/jpg/webp）
    fmt = None
    if target_format:
        to = target_format.lower()
        if to in {"jpg", "jpeg"}:
            to = "jpg"
        if to in {"png", "jpg", "webp"}:
            source = tinify.convert(source=source, convert={"type": f"image/{to}"})
            fmt = to

    result = source.result()
    out_data = result.to_buffer()

    width = result.width if hasattr(result, "width") else None
    height = result.height if hasattr(result, "height") else None

    return out_data, width, height, fmt


