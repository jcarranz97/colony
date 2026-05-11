from fastapi import status

from app.exceptions import AppExceptionError

from .constants import ErrorCode


class ActivityExceptionError(AppExceptionError):
    """Base exception for the activity / comments domain."""


class CommentNotFoundExceptionError(ActivityExceptionError):
    """Raised when a comment lookup misses or hits a soft-deleted row."""

    def __init__(self, comment_id: str | None = None) -> None:
        details = {"comment_id": comment_id} if comment_id else {}
        super().__init__(
            error_code=ErrorCode.COMMENT_NOT_FOUND,
            message="Comment not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class CommentNotAuthorExceptionError(ActivityExceptionError):
    """Raised when a user tries to edit a comment they didn't author."""

    def __init__(self, comment_id: str) -> None:
        super().__init__(
            error_code=ErrorCode.COMMENT_NOT_AUTHOR,
            message="Only the comment author can edit this comment",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"comment_id": comment_id},
        )


class CommentDeleteForbiddenExceptionError(ActivityExceptionError):
    """Raised when a non-author non-admin tries to delete a comment."""

    def __init__(self, comment_id: str) -> None:
        super().__init__(
            error_code=ErrorCode.COMMENT_DELETE_FORBIDDEN,
            message="Only the author or an admin can delete this comment",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"comment_id": comment_id},
        )


class InvalidEntityTypeExceptionError(ActivityExceptionError):
    """Raised when an entity_type is not commentable."""

    def __init__(self, entity_type: str) -> None:
        super().__init__(
            error_code=ErrorCode.INVALID_ENTITY_TYPE,
            message=f"Invalid entity type: {entity_type}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"entity_type": entity_type},
        )


class InvalidEntityReferenceExceptionError(ActivityExceptionError):
    """Raised when (entity_type, entity_id) doesn't resolve to an entity."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            error_code=ErrorCode.INVALID_ENTITY_REFERENCE,
            message=(f"No {entity_type} with id {entity_id} found in this household"),
            status_code=status.HTTP_404_NOT_FOUND,
            details={"entity_type": entity_type, "entity_id": entity_id},
        )


class CommentBodyRequiredExceptionError(ActivityExceptionError):
    """Raised when a comment body is empty or whitespace-only."""

    def __init__(self) -> None:
        super().__init__(
            error_code=ErrorCode.COMMENT_BODY_REQUIRED,
            message="Comment body cannot be empty",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
