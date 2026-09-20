"""
Ridgeline — Hiking Loadout Recommender

A local-first, LAN-only web application that recommends hiking gear based on
routes, weather, and personal preferences.
"""

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.config import PORT
from app.database import init_db
from app.routers import routes, loadout, health

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

app = FastAPI(
    title="Ridgeline",
    description="Hiking loadout recommendation engine",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(routes.router)
app.include_router(loadout.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
async def root():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


def main():
    uvicorn.run(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
