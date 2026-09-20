"""
Database setup and session management.
"""

import sqlite3
from pathlib import Path
from app.config import DB_PATH

conn: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    global conn
    if conn is None:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema."""
    db = get_connection()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            distance_km REAL,
            ascent_m REAL,
            high_point_m REAL,
            expected_duration_min REAL,
            exposure TEXT,
            gpx_hash TEXT,
            gpx_revision INTEGER DEFAULT 1,
            last_walked TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS route_revisions (
            id INTEGER PRIMARY KEY,
            route_id INTEGER NOT NULL,
            gpx_hash TEXT NOT NULL,
            revision INTEGER NOT NULL,
            imported_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (route_id) REFERENCES routes(id)
        );

        CREATE TABLE IF NOT EXISTS forecast_snapshots (
            id INTEGER PRIMARY KEY,
            route_id INTEGER NOT NULL,
            fetched_at TEXT DEFAULT (datetime('now')),
            valley_temp_min REAL,
            valley_temp_max REAL,
            high_route_temp_min REAL,
            high_route_temp_max REAL,
            rain_prob REAL,
            rain_amount_mm REAL,
            wind_speed_mph REAL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (route_id) REFERENCES routes(id)
        );

        CREATE TABLE IF NOT EXISTS recommendation_runs (
            id INTEGER PRIMARY KEY,
            route_id INTEGER NOT NULL,
            forecast_snapshot_id INTEGER,
            planned_loadout_id INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            confidence TEXT,
            summary TEXT,
            FOREIGN KEY (route_id) REFERENCES routes(id),
            FOREIGN KEY (forecast_snapshot_id) REFERENCES forecast_snapshots(id)
        );

        CREATE TABLE IF NOT EXISTS gear_items (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            type TEXT,
            category TEXT,
            role TEXT,
            capabilities TEXT,
            owner TEXT DEFAULT 'andy',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS recommendation_items (
            id INTEGER PRIMARY KEY,
            run_id INTEGER NOT NULL,
            gear_item_id INTEGER NOT NULL,
            bucket TEXT NOT NULL,
            reason TEXT,
            cue TEXT,
            FOREIGN KEY (run_id) REFERENCES recommendation_runs(id),
            FOREIGN KEY (gear_item_id) REFERENCES gear_items(id)
        );

        CREATE TABLE IF NOT EXISTS planned_loadouts (
            id INTEGER PRIMARY KEY,
            run_id INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (run_id) REFERENCES recommendation_runs(id)
        );

        CREATE TABLE IF NOT EXISTS planned_items (
            id INTEGER PRIMARY KEY,
            loadout_id INTEGER NOT NULL,
            gear_item_id INTEGER NOT NULL,
            bucket TEXT NOT NULL,
            reason TEXT,
            FOREIGN KEY (loadout_id) REFERENCES planned_loadouts(id),
            FOREIGN KEY (gear_item_id) REFERENCES gear_items(id)
        );

        CREATE TABLE IF NOT EXISTS completions (
            id INTEGER PRIMARY KEY,
            route_id INTEGER NOT NULL,
            planned_loadout_id INTEGER,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            weather_notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (route_id) REFERENCES routes(id),
            FOREIGN KEY (planned_loadout_id) REFERENCES planned_loadouts(id)
        );

        CREATE TABLE IF NOT EXISTS field_reports (
            id INTEGER PRIMARY KEY,
            completion_id INTEGER NOT NULL,
            raw_notes TEXT,
            rain_actual TEXT,
            felt_temp TEXT,
            gear_test_result TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (completion_id) REFERENCES completions(id)
        );

        CREATE TABLE IF NOT EXISTS report_items (
            id INTEGER PRIMARY KEY,
            report_id INTEGER NOT NULL,
            gear_item_id INTEGER NOT NULL,
            worn INTEGER DEFAULT 0,
            carried INTEGER DEFAULT 0,
            used INTEGER DEFAULT 0,
            FOREIGN KEY (report_id) REFERENCES field_reports(id),
            FOREIGN KEY (gear_item_id) REFERENCES gear_items(id)
        );

        CREATE TABLE IF NOT EXISTS feedback_chips (
            id INTEGER PRIMARY KEY,
            report_id INTEGER NOT NULL,
            chip_text TEXT NOT NULL,
            FOREIGN KEY (report_id) REFERENCES field_reports(id)
        );

        CREATE TABLE IF NOT EXISTS gear_tests (
            id INTEGER PRIMARY KEY,
            item_id INTEGER NOT NULL,
            test_name TEXT NOT NULL,
            status TEXT,
            FOREIGN KEY (item_id) REFERENCES gear_items(id)
        );

        CREATE TABLE IF NOT EXISTS application_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version INTEGER DEFAULT 1,
            runs_hot INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS gear_source_snapshot (
            id INTEGER PRIMARY KEY,
            source_path_hash TEXT NOT NULL,
            captured_at TEXT DEFAULT (datetime('now')),
            item_count INTEGER
        );
    """)
    db.commit()
