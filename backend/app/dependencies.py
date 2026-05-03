# Import auth dependencies for global use
from app.auth.dependencies import (
    CurrentActiveUser,
    CurrentAdminUser,
    CurrentUser,
    get_current_active_user,
    get_current_admin_user,
    get_current_user,
)
from app.database import get_db
from app.households.dependencies import (
    CurrentActiveHousehold,
    get_current_active_household,
)

# Re-export for convenience
__all__ = [
    "CurrentActiveHousehold",
    "CurrentActiveUser",
    "CurrentAdminUser",
    "CurrentUser",
    "get_current_active_household",
    "get_current_active_user",
    "get_current_admin_user",
    "get_current_user",
    "get_db",
]
