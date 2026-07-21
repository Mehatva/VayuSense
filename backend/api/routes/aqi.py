"""
AQI Routes — Live AQI data for all stations in a city.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import asyncio
from data.fetchers.openaq_fetcher import OpenAQFetcher
from config import settings

router = APIRouter()


@router.get("/live")
async def get_live_aqi(city: str = Query(default="Delhi", description="City name")):
    """
    Get live AQI readings for all monitoring stations in a city.
    Data sourced from CPCB via OpenAQ API.
    """
    if city not in settings.cities:
        raise HTTPException(status_code=400, detail=f"City '{city}' not supported. Available: {list(settings.cities.keys())}")

    async with OpenAQFetcher(api_key=settings.openaq_api_key) as fetcher:
        measurements = await fetcher.get_latest_measurements(city)
        stations = fetcher.parse_latest_to_station_dict(measurements)

    if not stations:
        # Return demo data if API fails (ensures demo always works)
        return _demo_stations(city)

    return {
        "city": city,
        "station_count": len(stations),
        "stations": list(stations.values()),
        "city_avg_aqi": _compute_city_avg(stations),
        "worst_ward": _find_worst(stations),
        "source": "OpenAQ / CPCB",
    }


@router.get("/summary")
async def get_city_summary(city: str = Query(default="Delhi")):
    """Get a quick AQI summary card for the city — used by citizen PWA."""
    async with OpenAQFetcher(api_key=settings.openaq_api_key) as fetcher:
        measurements = await fetcher.get_latest_measurements(city)
        stations = fetcher.parse_latest_to_station_dict(measurements)

    avg_aqi = _compute_city_avg(stations)

    from data.fetchers.openaq_fetcher import get_aqi_category
    return {
        "city": city,
        "current_aqi": avg_aqi,
        "category": get_aqi_category(avg_aqi) if avg_aqi else "Unknown",
        "station_count": len(stations),
        "health_advice": _get_health_advice(avg_aqi),
        "emoji": _get_aqi_emoji(avg_aqi),
    }


@router.get("/heatmap")
async def get_heatmap_data(city: str = Query(default="Delhi")):
    """
    Returns GeoJSON-compatible station data for Leaflet.js heatmap rendering.
    Each point has lat, lon, AQI value, and metadata.
    """
    async with OpenAQFetcher(api_key=settings.openaq_api_key) as fetcher:
        measurements = await fetcher.get_latest_measurements(city)
        stations = fetcher.parse_latest_to_station_dict(measurements)

    if not stations:
        stations = _demo_stations(city)["stations"]
        stations = {s["station_id"]: s for s in stations}

    features = []
    for s in stations.values():
        if s.get("latitude") and s.get("longitude") and s.get("aqi"):
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [s["longitude"], s["latitude"]]
                },
                "properties": {
                    "station_id": s["station_id"],
                    "station_name": s["station_name"],
                    "aqi": s["aqi"],
                    "category": s["aqi_category"],
                    "pm25": s.get("pm25"),
                    "pm10": s.get("pm10"),
                    "no2": s.get("no2"),
                    "color": _aqi_to_color(s["aqi"]),
                    "radius": _aqi_to_radius(s["aqi"]),
                }
            })

    return {
        "type": "FeatureCollection",
        "city": city,
        "features": features,
        "count": len(features),
    }


# ── Helpers ──────────────────────────────────────────────────────────────────

def _compute_city_avg(stations: dict) -> Optional[int]:
    aqis = [s["aqi"] for s in stations.values() if s.get("aqi")]
    return int(sum(aqis) / len(aqis)) if aqis else None

def _find_worst(stations: dict) -> Optional[dict]:
    valid = [s for s in stations.values() if s.get("aqi")]
    if not valid:
        return None
    worst = max(valid, key=lambda s: s["aqi"])
    return {"station": worst["station_name"], "aqi": worst["aqi"], "category": worst["aqi_category"]}

def _aqi_to_color(aqi: int) -> str:
    if aqi <= 50:   return "#00e400"
    if aqi <= 100:  return "#ffff00"
    if aqi <= 200:  return "#ff7e00"
    if aqi <= 300:  return "#ff0000"
    if aqi <= 400:  return "#8f3f97"
    return "#7e0023"

def _aqi_to_radius(aqi: int) -> int:
    return min(8 + (aqi // 50), 24)

def _get_aqi_emoji(aqi: Optional[int]) -> str:
    if aqi is None: return "❓"
    if aqi <= 50:   return "🟢"
    if aqi <= 100:  return "🟡"
    if aqi <= 200:  return "🟠"
    if aqi <= 300:  return "🔴"
    return "🔴"

def _get_health_advice(aqi: Optional[int]) -> str:
    if aqi is None: return "Data unavailable."
    if aqi <= 50:   return "Air quality is good. Enjoy outdoor activities."
    if aqi <= 100:  return "Air quality is acceptable. Sensitive individuals should limit prolonged outdoor exertion."
    if aqi <= 200:  return "Unhealthy for sensitive groups. Children and elderly should reduce outdoor time."
    if aqi <= 300:  return "Unhealthy. Everyone should reduce outdoor activities. Wear N95 mask outdoors."
    return "Hazardous. Avoid all outdoor activities. Keep windows closed."

def _demo_stations(city: str) -> dict:
    """Fallback demo data when API is unavailable."""
    import random
    demo = {
        "Delhi": [
            {"station_id": "D1", "station_name": "Dwarka", "city": "Delhi", "ward": "Dwarka",
             "latitude": 28.5921, "longitude": 77.0460, "pm25": 89.2, "pm10": 142.5,
             "no2": 45.2, "aqi": 287, "aqi_category": "Poor", "time": "2026-07-21T10:00:00Z"},
            {"station_id": "D2", "station_name": "Rohini", "city": "Delhi", "ward": "Rohini",
             "latitude": 28.7495, "longitude": 77.0574, "pm25": 75.1, "pm10": 120.3,
             "no2": 38.5, "aqi": 242, "aqi_category": "Poor", "time": "2026-07-21T10:00:00Z"},
            {"station_id": "D3", "station_name": "Connaught Place", "city": "Delhi", "ward": "Connaught Place",
             "latitude": 28.6315, "longitude": 77.2167, "pm25": 52.3, "pm10": 88.1,
             "no2": 62.4, "aqi": 178, "aqi_category": "Moderate", "time": "2026-07-21T10:00:00Z"},
            {"station_id": "D4", "station_name": "Anand Vihar", "city": "Delhi", "ward": "Anand Vihar",
             "latitude": 28.6469, "longitude": 77.3158, "pm25": 102.4, "pm10": 165.7,
             "no2": 71.8, "aqi": 319, "aqi_category": "Very Poor", "time": "2026-07-21T10:00:00Z"},
            {"station_id": "D5", "station_name": "Okhla", "city": "Delhi", "ward": "Okhla",
             "latitude": 28.5494, "longitude": 77.2750, "pm25": 68.9, "pm10": 112.4,
             "no2": 55.1, "aqi": 223, "aqi_category": "Poor", "time": "2026-07-21T10:00:00Z"},
        ]
    }
    stations_list = demo.get(city, demo["Delhi"])
    return {
        "city": city,
        "station_count": len(stations_list),
        "stations": stations_list,
        "city_avg_aqi": int(sum(s["aqi"] for s in stations_list) / len(stations_list)),
        "worst_ward": max(stations_list, key=lambda s: s["aqi"])["station_name"],
        "source": "Demo Data",
    }
