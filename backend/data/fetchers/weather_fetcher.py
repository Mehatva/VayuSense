"""
Weather Data Fetcher
Uses Open-Meteo API — completely free, no API key required.
Fetches current weather, forecasts, and historical data including
the critical Atmospheric Boundary Layer Height (ABLH).
Docs: https://open-meteo.com/en/docs
"""
import httpx
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)

OPEN_METEO_BASE = "https://api.open-meteo.com/v1"
OPEN_METEO_HISTORICAL = "https://archive-api.open-meteo.com/v1"


class WeatherFetcher:
    """
    Fetches weather data from Open-Meteo API.
    The Atmospheric Boundary Layer Height (ABLH) is the most critical
    variable for air quality — low ABLH traps pollutants near the ground.
    """

    HOURLY_VARIABLES = [
        "temperature_2m",
        "relative_humidity_2m",
        "wind_speed_10m",
        "wind_direction_10m",
        "precipitation",
        "boundary_layer_height",   # ← THE KEY VARIABLE for AQI
        "surface_pressure",
        "cloud_cover",
    ]

    AQI_VARIABLES = [
        "pm10",
        "pm2_5",
        "carbon_monoxide",
        "nitrogen_dioxide",
        "sulphur_dioxide",
        "ozone",
        "european_aqi",
        "us_aqi",
    ]

    def __init__(self):
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def get_current_and_forecast(
        self,
        lat: float,
        lon: float,
        forecast_days: int = 3
    ) -> dict:
        """
        Get current weather + 72-hour forecast.
        Returns: dict with 'current' and 'hourly' DataFrames.
        """
        try:
            resp = await self.client.get(
                f"{OPEN_METEO_BASE}/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "hourly": ",".join(self.HOURLY_VARIABLES),
                    "current": ",".join(self.HOURLY_VARIABLES[:4]),
                    "forecast_days": forecast_days,
                    "timezone": "Asia/Kolkata",
                }
            )
            resp.raise_for_status()
            data = resp.json()

            hourly_df = pd.DataFrame(data.get("hourly", {}))
            if "time" in hourly_df.columns:
                hourly_df["time"] = pd.to_datetime(hourly_df["time"])
                hourly_df["is_forecast"] = True

            current = data.get("current", {})
            current["latitude"] = lat
            current["longitude"] = lon

            return {"current": current, "hourly": hourly_df}

        except Exception as e:
            logger.error(f"Failed to fetch weather forecast: {e}")
            return {"current": {}, "hourly": pd.DataFrame()}

    async def get_air_quality_forecast(self, lat: float, lon: float) -> pd.DataFrame:
        """
        Get Open-Meteo's own AQI forecast (useful as an additional feature).
        Note: We build our own forecast but use this as a reference input.
        """
        try:
            resp = await self.client.get(
                f"{OPEN_METEO_BASE}/air-quality",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "hourly": ",".join(self.AQI_VARIABLES),
                    "forecast_days": 3,
                    "timezone": "Asia/Kolkata",
                }
            )
            resp.raise_for_status()
            data = resp.json()

            df = pd.DataFrame(data.get("hourly", {}))
            if "time" in df.columns:
                df["time"] = pd.to_datetime(df["time"])

            return df

        except Exception as e:
            logger.error(f"Failed to fetch air quality forecast: {e}")
            return pd.DataFrame()

    async def get_historical_weather(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        Fetch historical hourly weather data for model training.
        start_date, end_date: 'YYYY-MM-DD' format
        """
        try:
            resp = await self.client.get(
                f"{OPEN_METEO_HISTORICAL}/archive",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "start_date": start_date,
                    "end_date": end_date,
                    "hourly": ",".join(self.HOURLY_VARIABLES),
                    "timezone": "Asia/Kolkata",
                }
            )
            resp.raise_for_status()
            data = resp.json()

            df = pd.DataFrame(data.get("hourly", {}))
            if "time" in df.columns:
                df["time"] = pd.to_datetime(df["time"])
                df["is_forecast"] = False

            logger.info(f"Fetched {len(df)} rows of historical weather "
                        f"from {start_date} to {end_date}")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch historical weather: {e}")
            return pd.DataFrame()

    def compute_dispersion_index(self, row: dict) -> float:
        """
        Compute a Pollution Dispersion Index (0-1) from weather variables.
        Higher = better dispersion = lower AQI expected.
        Lower = stagnant air = higher AQI expected.

        Key factors:
        - ABLH: higher boundary layer → better mixing
        - Wind speed: higher → better dispersion
        - Relative humidity: higher → worse (particulates grow hygroscopically)
        - Precipitation: any rain → good dispersion (washout)
        """
        ablh = row.get("boundary_layer_height", 500) or 500
        wind = row.get("wind_speed_10m", 5) or 5
        humidity = row.get("relative_humidity_2m", 60) or 60
        precip = row.get("precipitation", 0) or 0

        # Normalize each factor to 0-1
        ablh_score = min(ablh / 2000, 1.0)          # ABLH 0-2000m range
        wind_score = min(wind / 30, 1.0)             # Wind 0-30 km/h range
        humidity_score = 1.0 - (humidity / 100)      # Lower humidity = better
        precip_score = min(precip / 5, 1.0)          # Precipitation 0-5mm

        dispersion = (
            0.40 * ablh_score +
            0.35 * wind_score +
            0.15 * humidity_score +
            0.10 * precip_score
        )
        return round(dispersion, 3)
