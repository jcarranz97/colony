from enum import Enum


class ErrorCode(str, Enum):
    """Activity and comments error codes."""

    COMMENT_NOT_FOUND = "COMMENT_NOT_FOUND"
    COMMENT_NOT_AUTHOR = "COMMENT_NOT_AUTHOR"
    COMMENT_DELETE_FORBIDDEN = "COMMENT_DELETE_FORBIDDEN"
    INVALID_ENTITY_TYPE = "INVALID_ENTITY_TYPE"
    INVALID_ENTITY_REFERENCE = "INVALID_ENTITY_REFERENCE"
    COMMENT_BODY_REQUIRED = "COMMENT_BODY_REQUIRED"


class EntityType(str, Enum):
    """Polymorphic entity types that can have activity and comments attached."""

    PAYMENT_METHOD = "payment_method"
    RECURRENT_EXPENSE = "recurrent_expense"
    RECURRENT_INCOME = "recurrent_income"
    CYCLE = "cycle"
    CYCLE_EXPENSE = "cycle_expense"
    CYCLE_INCOME = "cycle_income"
    COMMENT = "comment"


class ActivityAction(str, Enum):
    """Semantic actions recorded in the activity log."""

    CREATED = "created"
    UPDATED = "updated"
    DEACTIVATED = "deactivated"
    REACTIVATED = "reactivated"
    MARKED_PAID = "marked_paid"
    MARKED_UNPAID = "marked_unpaid"
    STATUS_CHANGED = "status_changed"
    COMPLETED = "completed"
    COMMENTED = "commented"
    COMMENT_EDITED = "comment_edited"
    COMMENT_DELETED = "comment_deleted"


# Entity types that can be commented on (everything except comments themselves).
COMMENTABLE_ENTITY_TYPES: frozenset[EntityType] = frozenset(
    t for t in EntityType if t is not EntityType.COMMENT
)

MAX_COMMENT_BODY_LENGTH = 10_000
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
