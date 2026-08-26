"""InsightFace FaceAnalysis wrapper (model load + raw analyze)."""

from __future__ import annotations

import logging
import threading
from typing import Optional

import numpy as np

from app.config import FaceAuthConfig, get_config
from app.core.exceptions import ModelNotReadyError
from app.core.models import DetectedFace
from app.services.engine.image_decode import decode_image_base64, decode_image_bytes

logger = logging.getLogger(__name__)


class InsightFaceEngine:
    """
    Singleton around insightface.app.FaceAnalysis.

    Responsibilities:
    - load buffalo_* models once
    - decode images
    - return DetectedFace list (bbox + score + embedding + landmarks)

    Higher-level business rules (single-face policy, enroll/verify) live in
    services/detection, services/embedding, and services/enrollment.
    """

    _instance: Optional["InsightFaceEngine"] = None
    _lock = threading.Lock()

    def __init__(self, config: Optional[FaceAuthConfig] = None):
        self.config = config or get_config()
        self._app = None
        self._ready = False

    @classmethod
    def get(cls, config: Optional[FaceAuthConfig] = None) -> "InsightFaceEngine":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._instance = None

    @property
    def ready(self) -> bool:
        return self._ready

    def load(self) -> None:
        if self._ready:
            return
        with self._lock:
            if self._ready:
                return
            try:
                from insightface.app import FaceAnalysis
            except ImportError as exc:
                raise ModelNotReadyError(
                    "insightface is not installed. pip install -r requirements.txt"
                ) from exc

            logger.info(
                "Loading InsightFace model=%s ctx_id=%s det_size=%s",
                self.config.model_name,
                self.config.ctx_id,
                self.config.det_size,
            )
            try:
                app = FaceAnalysis(
                    name=self.config.model_name,
                    providers=self._providers(),
                )
                app.prepare(
                    ctx_id=self.config.ctx_id,
                    det_size=self.config.det_size,
                )
            except Exception as exc:  # noqa: BLE001
                raise ModelNotReadyError(
                    f"Failed to load InsightFace model: {exc}"
                ) from exc

            self._app = app
            self._ready = True
            logger.info("InsightFace ready")

    def _providers(self) -> list[str]:
        if self.config.ctx_id >= 0:
            return ["CUDAExecutionProvider", "CPUExecutionProvider"]
        return ["CPUExecutionProvider"]

    def decode_image(
        self,
        *,
        image_base64: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
    ) -> np.ndarray:
        max_bytes = self.config.max_image_bytes
        if image_bytes is not None:
            return decode_image_bytes(image_bytes, max_bytes=max_bytes)
        if image_base64 is None:
            from app.core.exceptions import InvalidImageError

            raise InvalidImageError("image_base64 or image_bytes is required")
        return decode_image_base64(image_base64, max_bytes=max_bytes)

    def analyze(
        self,
        image_bgr: np.ndarray,
        *,
        max_faces: Optional[int] = None,
    ) -> list[DetectedFace]:
        self.load()
        if self._app is None:
            raise ModelNotReadyError("InsightFace model is not loaded")

        raw_faces = self._app.get(image_bgr) or []
        raw_faces = sorted(
            raw_faces, key=lambda f: float(f.det_score), reverse=True
        )
        if max_faces is not None:
            raw_faces = raw_faces[:max_faces]

        results: list[DetectedFace] = []
        for face in raw_faces:
            emb = np.asarray(face.embedding, dtype=np.float32).reshape(-1)
            norm = float(np.linalg.norm(emb))
            if norm > 0:
                emb = emb / norm

            landmarks = None
            if getattr(face, "kps", None) is not None:
                landmarks = np.asarray(face.kps, dtype=np.float32).tolist()

            bbox = [
                float(x)
                for x in np.asarray(face.bbox, dtype=np.float32).tolist()
            ]
            results.append(
                DetectedFace(
                    bbox=bbox,
                    score=float(face.det_score),
                    embedding=emb.astype(float).tolist(),
                    landmarks=landmarks,
                )
            )
        return results
