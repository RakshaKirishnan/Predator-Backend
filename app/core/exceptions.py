"""Domain exceptions."""

from __future__ import annotations


class FaceAuthError(Exception):
    code: str = "face_auth_error"
    http_status: int = 400

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class InvalidImageError(FaceAuthError):
    code = "invalid_image"
    http_status = 400


class NoFaceDetectedError(FaceAuthError):
    code = "no_face_detected"
    http_status = 400


class MultipleFacesError(FaceAuthError):
    code = "multiple_faces"
    http_status = 400


class ModelNotReadyError(FaceAuthError):
    code = "model_not_ready"
    http_status = 503


class StorageError(FaceAuthError):
    code = "storage_error"
    http_status = 500


class EmbeddingMismatchError(FaceAuthError):
    code = "embedding_mismatch"
    http_status = 400


class UserAlreadyExistsError(FaceAuthError):
    code = "user_already_exists"
    http_status = 409


class FaceLoginFailedError(FaceAuthError):
    code = "face_login_failed"
    http_status = 401


class InviteInvalidError(FaceAuthError):
    code = "invite_invalid"
    http_status = 400


class InviteExpiredError(FaceAuthError):
    code = "invite_expired"
    http_status = 400


class UnauthorizedError(FaceAuthError):
    code = "unauthorized"
    http_status = 401


class ForbiddenError(FaceAuthError):
    code = "forbidden"
    http_status = 403


class EmailSendError(FaceAuthError):
    code = "email_send_failed"
    http_status = 502
