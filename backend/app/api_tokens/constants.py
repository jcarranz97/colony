from enum import Enum


class ErrorCode(str, Enum):
    """API token error codes."""

    API_TOKEN_NOT_FOUND = "API_TOKEN_NOT_FOUND"


# Every personal access token starts with this prefix. The auth dependency
# uses it to tell a PAT apart from a JWT without a database lookup.
TOKEN_PREFIX = "colony_pat_"

# Number of random bytes used for the token secret (token_urlsafe encodes
# roughly 1.3 characters per byte, so 32 bytes → a ~43-char secret).
TOKEN_SECRET_BYTES = 32

# Leading characters stored in plaintext so the UI can identify a token
# after creation (e.g. "colony_pat_AbC").
TOKEN_DISPLAY_PREFIX_LENGTH = 16

# Maximum length of the user-supplied token label.
MAX_TOKEN_NAME_LENGTH = 100
