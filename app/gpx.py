"""
GPX file parsing and analysis.

Parses GPX files to extract route geometry, elevation profile, and basic
statistics (distance, ascent, high point).
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

import gpxpy
from gpxpy.geo import haversine_distance


def hash_gpx_content(content: bytes) -> str:
    """Content-hash a GPX file for stable identity."""
    return hashlib.sha256(content).hexdigest()


def parse_gpx(content: bytes) -> dict[str, Any]:
    """
    Parse GPX content and extract route metrics.

    Returns a dict with:
    - gpx_hash: content hash
    - distance_km: total distance in km
    - ascent_m: total ascent in metres
    - high_point_m: maximum elevation in metres
    - num_points: number of track points
    - track_segments: count of track segments
    """
    gpx = gpxpy.parse(content.decode("utf-8"))
    distance = 0.0
    ascent = 0.0
    descent = 0.0
    high_point = 0.0
    points = 0

    for track in gpx.tracks:
        for segment in track.segments:
            points += len(segment.points)
            for i, pt in enumerate(segment.points):
                if i > 0:
                    distance += haversine_distance(
                        segment.points[i - 1].latitude,
                        segment.points[i - 1].longitude,
                        pt.latitude,
                        pt.longitude,
                    )
                if pt.elevation is not None:
                    if pt.elevation > high_point:
                        high_point = pt.elevation
                    if i > 0 and segment.points[i - 1].elevation is not None:
                        diff = pt.elevation - segment.points[i - 1].elevation
                        if diff > 0:
                            ascent += diff
                        else:
                            descent += abs(diff)

    distance_km = distance / 1000.0
    high_point_m = high_point

    return {
        "gpx_hash": "",
        "distance_km": round(distance_km, 1),
        "ascent_m": round(ascent, 0),
        "high_point_m": round(high_point_m, 0) if high_point_m else None,
        "num_points": points,
        "track_segments": len(gpx.tracks[0].segments) if gpx.tracks else 0,
    }


def analyze_gpx_file(file_path: Path) -> dict[str, Any]:
    """Analyze a GPX file and return metrics with content hash."""
    content = file_path.read_bytes()
    metrics = parse_gpx(content)
    metrics["gpx_hash"] = hash_gpx_content(content)
    metrics["file_name"] = file_path.name
    metrics["parsed_at"] = datetime.now().isoformat()
    return metrics
