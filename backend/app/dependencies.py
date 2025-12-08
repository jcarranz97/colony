from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db

# Import auth dependencies for global use
from app.auth.dependencies import get_current_user, get_current_active_user, CurrentUser, CurrentActiveUser

# Re-export for convenience
__all__ = [
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "CurrentUser",
    "CurrentActiveUser"
]
