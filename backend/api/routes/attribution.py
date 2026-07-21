"""
Source Attribution Routes
Returns % contribution of each source category to current AQI per ward.
"""
from fastapi import APIRouter, Query
from typing import Optional
from models.attribution import AttributionModel

router = APIRouter()
_model = AttributionModel()


@router.get("/{ward}")
async def get_ward_attribution(
    ward: str,
    city: str = Query(default="Delhi"),
):
    """
    Get source attribution breakdown for a specific ward.
    Returns % contribution per source category with confidence scores.
    """
    result = await _model.get_attribution(city=city, ward=ward)
    return result


@router.get("/city/{city}")
async def get_city_attribution(city: str):
    """
    Get attribution for all wards in a city.
    Used for the full heatmap overlay.
    """
    result = await _model.get_city_attribution(city=city)
    return result
