"""
Forecast Routes — 72-hour AQI forecast at ward level.
"""
from fastapi import APIRouter, Query
from models.forecast import ForecastModel

router = APIRouter()
_model = ForecastModel()


@router.get("/{ward}")
async def get_ward_forecast(
    ward: str,
    city: str = Query(default="Delhi"),
    hours: int = Query(default=72, le=72),
):
    """
    Get 72-hour hourly AQI forecast for a specific ward.
    Powered by Temporal Fusion Transformer trained on 5 years of CPCB data.
    """
    return await _model.forecast_ward(city=city, ward=ward, hours=hours)


@router.get("/grid/{city}")
async def get_city_grid_forecast(
    city: str,
    hour_offset: int = Query(default=6, description="Hours from now to forecast"),
):
    """
    Get AQI forecast for the entire city grid at a specific future hour.
    Used to render the forecast slider on the dashboard map.
    """
    return await _model.forecast_city_grid(city=city, hour_offset=hour_offset)
