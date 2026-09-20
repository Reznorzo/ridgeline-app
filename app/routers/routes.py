"""
Route management endpoints.
"""

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from app.database import get_connection
from app.schemas import RouteCreate, RouteOut, GPXImportOut
from app.gpx import analyze_gpx_file

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=list[RouteOut])
async def list_routes():
    db = get_connection()
    rows = db.execute("SELECT * FROM routes ORDER BY name").fetchall()
    return [dict(row) for row in rows]


@router.get("/{route_id}", response_model=RouteOut)
async def get_route(route_id: int):
    db = get_connection()
    row = db.execute("SELECT * FROM routes WHERE id = ?", (route_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Route not found")
    return dict(row)


@router.post("", response_model=RouteOut)
async def create_route(route: RouteCreate):
    db = get_connection()
    cursor = db.execute(
        """INSERT INTO routes (name, distance_km, ascent_m, high_point_m,
           expected_duration_min, exposure)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (route.name, route.distance_km, route.ascent_m, route.high_point_m,
         route.expected_duration_min, route.exposure),
    )
    db.commit()
    row = db.execute("SELECT * FROM routes WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)


@router.post("/import-gpx", response_model=GPXImportOut)
async def import_gpx(file: UploadFile = File(...)):
    """Import a GPX file and create a route from it."""
    gpx_data = await file.read()
    if not gpx_data:
        raise HTTPException(status_code=400, detail="No GPX data provided")

    with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as f:
        f.write(gpx_data)
        temp_path = Path(f.name)

    try:
        metrics = analyze_gpx_file(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)

    route_name = Path(file.filename or metrics["file_name"]).stem

    db = get_connection()
    cursor = db.execute(
        """INSERT INTO routes (name, distance_km, ascent_m, high_point_m,
           gpx_hash, gpx_revision)
           VALUES (?, ?, ?, ?, ?, 1)""",
        (route_name, metrics["distance_km"], metrics["ascent_m"],
         metrics["high_point_m"], metrics["gpx_hash"]),
    )
    db.commit()

    return GPXImportOut(
        id=cursor.lastrowid,
        name=route_name,
        gpx_hash=metrics["gpx_hash"],
        distance_km=metrics["distance_km"],
        ascent_m=metrics["ascent_m"],
        high_point_m=metrics["high_point_m"],
    )
