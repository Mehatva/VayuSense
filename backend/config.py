"""
VayuSense — Central Configuration
All settings loaded from environment variables with sensible defaults.
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "VayuSense"
    app_version: str = "1.0.0"
    app_env: str = "development"
    app_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # Database
    db_user: str = "vayusense"
    db_password: str = "vayusense123"
    db_name: str = "vayusense"
    db_host: str = "localhost"
    db_port: int = 5432

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def database_url_sync(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # API Keys
    openaq_api_key: str = ""
    google_maps_api_key: str = ""
    gemini_api_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"

    # Cities config
    primary_city: str = "Delhi"
    primary_city_lat: float = 28.6139
    primary_city_lon: float = 77.2090

    # Cities supported
    cities: dict = {
        "Delhi": {"lat": 28.6139, "lon": 77.2090, "country": "IN", "openaq_name": "Delhi"},
        "Mumbai": {"lat": 19.0760, "lon": 72.8777, "country": "IN", "openaq_name": "Mumbai"},
        "Bengaluru": {"lat": 12.9716, "lon": 77.5946, "country": "IN", "openaq_name": "Bengaluru"},
        "Kolkata": {"lat": 22.5726, "lon": 88.3639, "country": "IN", "openaq_name": "Kolkata"},
        "Chennai": {"lat": 13.0827, "lon": 80.2707, "country": "IN", "openaq_name": "Chennai"},
    }

    # Economic damage constants (based on TERI & WHO methodology)
    cost_per_daly_usd: float = 1000.0
    inr_per_usd: float = 83.5
    daily_dalyperpoint_per_million: float = 0.0012  # DALYs per AQI point per million people per day
    productivity_loss_per_hour_inr: float = 185.0   # Average hourly wage India (2024)

    # AQI thresholds (CPCB India standard)
    aqi_good: int = 50
    aqi_satisfactory: int = 100
    aqi_moderate: int = 200
    aqi_poor: int = 300
    aqi_very_poor: int = 400
    aqi_severe: int = 500
    aqi_school_closure: int = 300

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
