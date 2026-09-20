"""
Ridgeline — Hiking Loadout Recommender

A local-first, LAN-only web application that recommends hiking gear based on
routes, weather, and personal preferences.
"""

import uvicorn
from fastapi import FastAPI
from app.config import PORT
from app.database import init_db
from app.routers import routes, loadout, health

app = FastAPI(
    title="Ridgeline",
    description="Hiking loadout recommendation engine",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(routes.router)
app.include_router(loadout.router)


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/")
async def root():
    return {"app": "Ridgeline", "version": "0.1.0"}


def main():
    uvicorn.run(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
