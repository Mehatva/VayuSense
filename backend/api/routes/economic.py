"""
Economic Damage Routes
Real-time economic cost of current pollution episode.
"""
from fastapi import APIRouter, Query
from models.economic import EconomicCalculator

router = APIRouter()
_calc = EconomicCalculator()


@router.get("/damage")
async def get_economic_damage(
    city: str = Query(default="Delhi"),
    hours_back: int = Query(default=48, description="Hours to look back for damage calculation"),
):
    """
    Compute the running economic cost of the current pollution episode.
    Returns healthcare costs, productivity losses, and life-years lost
    expressed in INR — updated in near real-time.

    Methodology: TERI + WHO DALY-based approach.
    """
    return await _calc.compute_damage(city=city, hours_back=hours_back)


@router.get("/live-tick")
async def get_live_tick(city: str = Query(default="Delhi")):
    """
    Lightweight endpoint for the live counter tick.
    Returns current total damage + per-minute rate.
    Called every 60 seconds by the WebSocket.
    """
    return await _calc.get_tick(city=city)
