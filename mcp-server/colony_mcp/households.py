"""Helpers for resolving households and aggregating across them.

Colony scopes data per household. These helpers let read tools default to
aggregating across every household the user belongs to, while still
allowing a single household to be targeted by name.
"""

from typing import Any

from .client import ColonyAPIError, colony_request


async def fetch_households() -> list[dict[str, Any]]:
    """Return every household the current user belongs to."""
    return await colony_request("GET", "/households/me")


async def resolve_household(name_or_id: str) -> tuple[str, str]:
    """Resolve a household name (case-insensitive) or UUID.

    Args:
        name_or_id: A household name or its UUID.

    Returns:
        A ``(household_id, household_name)`` tuple.

    Raises:
        ColonyAPIError: If nothing matches.
    """
    households = await fetch_households()
    needle = name_or_id.strip().lower()
    for household in households:
        if str(household["id"]) == name_or_id.strip() or (
            household["name"].lower() == needle
        ):
            return str(household["id"]), household["name"]

    available = ", ".join(h["name"] for h in households) or "none"
    raise ColonyAPIError(
        f"No household matches '{name_or_id}'. Your households: {available}."
    )


async def households_to_query(household: str | None) -> list[tuple[str, str]]:
    """Return the households a read tool should cover.

    Args:
        household: An optional household name/UUID. When ``None``, every
            household the user belongs to is returned (aggregate mode).

    Returns:
        A list of ``(household_id, household_name)`` tuples.
    """
    if household:
        return [await resolve_household(household)]
    return [(str(h["id"]), h["name"]) for h in await fetch_households()]


async def resolve_cycle_household_id(cycle_id: str) -> str:
    """Find which of the user's households owns a cycle.

    Cycle-scoped endpoints need the household, but agents only have the
    cycle id; this looks it up by probing each household the user belongs
    to.

    Args:
        cycle_id: UUID of the cycle.

    Returns:
        The owning household's UUID.

    Raises:
        ColonyAPIError: If the cycle is not found in any of the user's
            households.
    """
    for household_id, _ in await households_to_query(None):
        try:
            await colony_request(
                "GET",
                f"/cycles/{cycle_id}",
                params={"household_id": household_id},
            )
        except ColonyAPIError:
            continue
        return household_id

    raise ColonyAPIError(
        f"Cycle {cycle_id} was not found in any household you belong to."
    )
