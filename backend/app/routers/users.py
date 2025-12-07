from fastapi import APIRouter

router = APIRouter()


@router.get("/users/", tags=["users"])
async def read_users() -> list[dict]:
    """Retrieve a list of users."""
    return [{"username": "Rick"}, {"username": "Morty"}]


@router.get("/users/me", tags=["users"])
async def read_user_me() -> dict:
    """Retrieve the current user's information."""
    return {"username": "fakecurrentuser"}


@router.get("/users/{username}", tags=["users"])
async def read_user(username: str) -> dict:
    """Retrieve a specific user's information by username."""
    return {"username": username}
