"""Item management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_token_header

router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


fake_items_db = {"plumbus": {"name": "Plumbus"}, "gun": {"name": "Portal Gun"}}


@router.get("/")
async def read_items() -> dict:
    """Retrieve all items from the database.

    Returns:
        dict: Dictionary containing all available items

    Example:
        >>> await read_items()
        {"plumbus": {"name": "Plumbus"}, "gun": {"name": "Portal Gun"}}
    """
    return fake_items_db


@router.get("/{item_id}")
async def read_item(item_id: str) -> dict:
    """Retrieve a specific item by its ID.

    Args:
        item_id: The unique identifier of the item to retrieve

    Returns:
        dict: Item details including name and ID

    Raises:
        HTTPException: 404 error if item is not found

    Example:
        >>> await read_item("plumbus")
        {"name": "Plumbus", "item_id": "plumbus"}
    """
    if item_id not in fake_items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"name": fake_items_db[item_id]["name"], "item_id": item_id}


@router.put(
    "/{item_id}",
    tags=["custom"],
    responses={403: {"description": "Operation forbidden"}},
)
async def update_item(item_id: str) -> dict:
    """Update a specific item (restricted to 'plumbus' only).

    Args:
        item_id: The unique identifier of the item to update

    Returns:
        dict: Updated item details including ID and name

    Raises:
        HTTPException: 403 error if trying to update any item other than 'plumbus'

    Example:
        >>> await update_item("plumbus")
        {"item_id": "plumbus", "name": "The great Plumbus"}
    """
    if item_id != "plumbus":
        raise HTTPException(
            status_code=403, detail="You can only update the item: plumbus"
        )
    return {"item_id": item_id, "name": "The great Plumbus"}
