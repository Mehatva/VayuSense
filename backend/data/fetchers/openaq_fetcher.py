"""
OpenAQ Data Fetcher
Fetches live and historical AQI data from the OpenAQ API v3.
OpenAQ aggregates data from CPCB stations across India — no additional auth needed for free tier.
Docs: https://docs.openaq.org/
"""
import httpx
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)

OPENAQ_BASE = "https://api.openaq.org/v3"

# OpenAQ location IDs for major Indian cities (pre-resolved)
CITY_LOCATION_IDS = {
    "Delhi": None,      # Will be resolved dynamically
    "Mumbai": None,
    "Bengaluru": None,
    "Kolkata": None,
    "Chennai": None,
}

# CPCB AQI breakpoints (India standard — different from US EPA)
AQI_BREAKPOINTS = {
    "pm25": [
        (0, 30, 0, 50),
        (31, 60, 51, 100),
        (61, 90, 101, 200),
        (91, 120, 201, 300),
        (121, 250, 301, 400),
        (251, float('inf'), 401, 500),
    ],
    "pm10": [
        (0, 50, 0, 50),
        (51, 100, 51, 100),
        (101, 250, 101, 200),
        (251, 350, 201, 300),
        (351, 430, 301, 400),
        (431, float('inf'), 401, 500),
    ],
}

AQI_CATEGORIES = [
    (0, 50, "Good"),
    (51, 100, "Satisfactory"),
    (101, 200, "Moderate"),
    (201, 300, "Poor"),
    (301, 400, "Very Poor"),
    (401, 500, "Severe"),
]


def compute_cpcb_aqi(concentration: float, pollutant: str) -> Optional[int]:
    """Compute CPCB AQI from pollutant concentration using Indian breakpoints."""
    if concentration is None or concentration < 0:
        return None

    breakpoints = AQI_BREAKPOINTS.get(pollutant)
    if not breakpoints:
        return None

    for (c_low, c_high, aqi_low, aqi_high) in breakpoints:
        if c_low <= concentration <= c_high:
            aqi = ((aqi_high - aqi_low) / (c_high - c_low)) * (concentration - c_low) + aqi_low
            return int(round(aqi))

    return 500  # Severe beyond scale


def get_aqi_category(aqi: int) -> str:
    for (low, high, cat) in AQI_CATEGORIES:
        if low <= aqi <= high:
            return cat
    return "Severe"


class OpenAQFetcher:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key} if api_key else {}
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url=OPENAQ_BASE,
            headers=self.headers,
            timeout=30.0
        )
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def get_locations_for_city(self, city: str, country: str = "IN") -> list[dict]:
        """Get all monitoring station locations for a given city."""
        try:
            resp = await self.client.get(
                "/locations",
                params={
                    "city": city,
                    "country": country,
                    "limit": 100,
                    "isMobile": False,
                    "isMonitor": True,
                }
            )
            resp.raise_for_status()
            data = resp.json()
            locations = data.get("results", [])
            logger.info(f"Found {len(locations)} stations for {city}")
            return locations
        except Exception as e:
            logger.error(f"Failed to fetch locations for {city}: {e}")
            return []

    async def get_latest_measurements(self, city: str, country: str = "IN") -> list[dict]:
        """Get the latest AQI measurements for all stations in a city."""
        try:
            resp = await self.client.get(
                "/measurements",
                params={
                    "city": city,
                    "country": country,
                    "limit": 500,
                    "parameters": "pm25,pm10,no2,so2,co,o3",
                    "sort": "desc",
                    "order_by": "datetime",
                }
            )
            resp.raise_for_status()
            data = resp.json()
            measurements = data.get("results", [])
            logger.info(f"Fetched {len(measurements)} latest measurements for {city}")
            return measurements
        except Exception as e:
            logger.error(f"Failed to fetch latest measurements for {city}: {e}")
            return []

    async def get_historical_measurements(
        self,
        city: str,
        days_back: int = 30,
        country: str = "IN"
    ) -> pd.DataFrame:
        """Fetch historical AQI data for model training."""
        date_from = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
        date_to = datetime.now(timezone.utc).isoformat()

        all_measurements = []
        page = 1

        while True:
            try:
                resp = await self.client.get(
                    "/measurements",
                    params={
                        "city": city,
                        "country": country,
                        "date_from": date_from,
                        "date_to": date_to,
                        "parameters": "pm25,pm10,no2",
                        "limit": 1000,
                        "page": page,
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])

                if not results:
                    break

                all_measurements.extend(results)
                page += 1

                if page > 20:  # Safety limit
                    break

                await asyncio.sleep(0.3)  # Rate limiting

            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break

        logger.info(f"Total historical measurements fetched: {len(all_measurements)}")
        return self._parse_measurements_to_df(all_measurements)

    def _parse_measurements_to_df(self, measurements: list) -> pd.DataFrame:
        """Parse OpenAQ measurement list into a clean DataFrame."""
        rows = []
        for m in measurements:
            row = {
                "time": m.get("date", {}).get("utc"),
                "station_id": str(m.get("locationId", "")),
                "station_name": m.get("location", ""),
                "city": m.get("city", ""),
                "latitude": m.get("coordinates", {}).get("latitude"),
                "longitude": m.get("coordinates", {}).get("longitude"),
                "parameter": m.get("parameter", ""),
                "value": m.get("value"),
                "unit": m.get("unit", ""),
            }
            rows.append(row)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df["time"] = pd.to_datetime(df["time"], utc=True)

        # Pivot: one row per (time, station), columns = parameters
        df_pivot = df.pivot_table(
            index=["time", "station_id", "station_name", "city", "latitude", "longitude"],
            columns="parameter",
            values="value",
            aggfunc="mean"
        ).reset_index()

        df_pivot.columns.name = None

        # Compute AQI from available pollutants
        if "pm25" in df_pivot.columns:
            df_pivot["aqi_pm25"] = df_pivot["pm25"].apply(
                lambda x: compute_cpcb_aqi(x, "pm25") if pd.notna(x) else None
            )
        if "pm10" in df_pivot.columns:
            df_pivot["aqi_pm10"] = df_pivot["pm10"].apply(
                lambda x: compute_cpcb_aqi(x, "pm10") if pd.notna(x) else None
            )

        # Overall AQI = max of individual pollutant AQIs
        aqi_cols = [c for c in ["aqi_pm25", "aqi_pm10"] if c in df_pivot.columns]
        if aqi_cols:
            df_pivot["aqi"] = df_pivot[aqi_cols].max(axis=1).astype("Int64")
            df_pivot["aqi_category"] = df_pivot["aqi"].apply(
                lambda x: get_aqi_category(x) if pd.notna(x) else "Unknown"
            )

        return df_pivot

    def parse_latest_to_station_dict(self, measurements: list) -> dict:
        """
        Parse latest measurements into a clean dict keyed by station_id.
        Used for the live dashboard endpoint.
        """
        stations = {}
        for m in measurements:
            sid = str(m.get("locationId", ""))
            if sid not in stations:
                stations[sid] = {
                    "station_id": sid,
                    "station_name": m.get("location", ""),
                    "city": m.get("city", ""),
                    "latitude": m.get("coordinates", {}).get("latitude"),
                    "longitude": m.get("coordinates", {}).get("longitude"),
                    "time": m.get("date", {}).get("utc"),
                    "pm25": None, "pm10": None, "no2": None,
                    "so2": None, "co": None, "o3": None,
                }
            param = m.get("parameter")
            value = m.get("value")
            if param in ["pm25", "pm10", "no2", "so2", "co", "o3"]:
                stations[sid][param] = value

        # Compute AQI for each station
        for sid, s in stations.items():
            aqi_vals = []
            if s["pm25"] is not None:
                v = compute_cpcb_aqi(s["pm25"], "pm25")
                if v:
                    aqi_vals.append(v)
            if s["pm10"] is not None:
                v = compute_cpcb_aqi(s["pm10"], "pm10")
                if v:
                    aqi_vals.append(v)
            s["aqi"] = max(aqi_vals) if aqi_vals else None
            s["aqi_category"] = get_aqi_category(s["aqi"]) if s["aqi"] else "Unknown"

        return stations
