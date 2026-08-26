"""Decode browser captures (data URL / raw base64) into OpenCV BGR images."""

from __future__ import annotations

import base64

import cv2
import numpy as np

from app.core.exceptions import InvalidImageError


def decode_image_base64(
    image_base64: str,
    *,
    max_bytes: int,
) -> np.ndarray:
    if not image_base64 or not str(image_base64).strip():
        raise InvalidImageError("image_base64 is required")

    payload = image_base64.strip()
    if payload.startswith("data:"):
        comma = payload.find(",")
        if comma < 0:
            raise InvalidImageError("Invalid data URL (missing comma)")
        payload = payload[comma + 1 :]

    payload = "".join(payload.split())
    try:
        image_bytes = base64.b64decode(payload, validate=False)
    except Exception as exc:  # noqa: BLE001
        raise InvalidImageError("Invalid base64 image payload") from exc

    return decode_image_bytes(image_bytes, max_bytes=max_bytes)


def decode_image_bytes(image_bytes: bytes, *, max_bytes: int) -> np.ndarray:
    if not image_bytes:
        raise InvalidImageError("Empty image bytes")
    if len(image_bytes) > max_bytes:
        raise InvalidImageError(
            f"Image exceeds max size of {max_bytes} bytes"
        )

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise InvalidImageError("Could not decode image bytes as JPEG/PNG")
    return bgr
