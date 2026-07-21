"""
Enforcement Intelligence Routes
AI-generated ranked enforcement action list with evidence briefs.
"""
from fastapi import APIRouter, Query
from models.enforcement import EnforcementAgent

router = APIRouter()
_agent = EnforcementAgent()


@router.get("/actions")
async def get_enforcement_actions(
    city: str = Query(default="Delhi"),
    top_n: int = Query(default=5, le=20),
):
    """
    Get today's top enforcement action recommendations.
    Each action includes: target site, priority score, projected AQI improvement,
    evidence brief, legal basis, and optimal inspection window.
    This is the output of the multi-step agentic reasoning pipeline.
    """
    return await _agent.generate_actions(city=city, top_n=top_n)


@router.get("/impact/{source_id}")
async def get_counterfactual_impact(
    source_id: int,
    city: str = Query(default="Delhi"),
):
    """
    Counterfactual: 'If we shut down this source tonight,
    how much does the AQI drop in downwind wards by morning?'
    Used for the Policy Simulator partial preview.
    """
    return await _agent.compute_counterfactual(city=city, source_id=source_id)
