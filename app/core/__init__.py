"""Core package."""

from app.core.exceptions import (
    EmailSendError,
    EmbeddingMismatchError,
    FaceAuthError,
    FaceLoginFailedError,
    ForbiddenError,
    InvalidImageError,
    InviteExpiredError,
    InviteInvalidError,
    ModelNotReadyError,
    MultipleFacesError,
    NoFaceDetectedError,
    StorageError,
    UnauthorizedError,
    UserAlreadyExistsError,
)
from app.core.models import DetectedFace, MatchResult

__all__ = [
    "DetectedFace",
    "MatchResult",
    "FaceAuthError",
    "InvalidImageError",
    "NoFaceDetectedError",
    "MultipleFacesError",
    "ModelNotReadyError",
    "StorageError",
    "EmbeddingMismatchError",
    "UserAlreadyExistsError",
    "FaceLoginFailedError",
    "InviteInvalidError",
    "InviteExpiredError",
    "UnauthorizedError",
    "ForbiddenError",
    "EmailSendError",
]
