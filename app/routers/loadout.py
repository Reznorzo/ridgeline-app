"""
Loadout recommendation endpoints.
"""

from fastapi import APIRouter, HTTPException

from app.database import get_connection
from app.obsidian import read_gear_vault
from app.schemas import GearItemOut, RecommendationOut
from app.services.recommend import generate_recommendation

router = APIRouter(prefix="/loadout", tags=["loadout"])


@router.get("/recommend/{route_id}", response_model=RecommendationOut)
async def recommend(route_id: int):
    """Generate a loadout recommendation for a route."""
    db = get_connection()

    route = db.execute("SELECT * FROM routes WHERE id = ?", (route_id,)).fetchone()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # Get the latest forecast snapshot
    forecast = db.execute(
        """SELECT * FROM forecast_snapshots
           WHERE route_id = ? ORDER BY fetched_at DESC LIMIT 1""",
        (route_id,),
    ).fetchone()

    forecast_dict = dict(forecast) if forecast else {}

    # Read gear from Obsidian vault
    vault_result = read_gear_vault()
    gear_items = vault_result.items

    if not gear_items:
        raise HTTPException(status_code=503, detail="No gear items loaded from Obsidian vault")

    exposure = route["exposure"] or "mixed"

    rec = generate_recommendation(
        route=dict(route),
        forecast=forecast_dict,
        gear_items=gear_items,
        exposure=exposure,
    )

    return RecommendationOut(
        items=[{"gear_item": item.gear_item.to_dict(), "bucket": item.bucket,
                "reason": item.reason, "cue": item.cue,
                "decisive_factors": item.decisive_factors, "caveats": item.caveats,
                "depends_on_gear_ids": item.depends_on_gear_ids,
                "combination_reason": item.combination_reason} for item in rec.items],
        confidence=rec.confidence,
        summary=rec.summary,
        conditions=rec.conditions,
        policy_version=rec.policy_version,
        warnings=rec.warnings,
    )


@router.get("/gear", response_model=list[GearItemOut])
async def list_gear():
    """List all gear items loaded from the Obsidian vault."""
    vault_result = read_gear_vault()
    return [item.to_dict() for item in vault_result.items]
