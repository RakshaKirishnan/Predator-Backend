"""Extract a single-face InsightFace embedding from an image (server-side only)."""

from __future__ import annotations

from app.core.exceptions import MultipleFacesError, NoFaceDetectedError
from app.core.models import DetectedFace
from app.services.engine.insightface_engine import InsightFaceEngine


class FaceEmbeddingService:
    """Backend owns embedding generation — never trust client-sent vectors."""

    def __init__(self, engine: InsightFaceEngine):
        self.engine = engine

    def from_image_base64(self, image_base64: str) -> DetectedFace:
        image = self.engine.decode_image(image_base64=image_base64)
        faces = self.engine.analyze(image, max_faces=None)
        if not faces:
            raise NoFaceDetectedError("No face detected in the uploaded image")
        if len(faces) > 1:
            raise MultipleFacesError(
                "Multiple faces detected; exactly one face is required"
            )
        return faces[0]
