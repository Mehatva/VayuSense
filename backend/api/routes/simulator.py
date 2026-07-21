"""
Policy Simulator Route — The "What If" Differentiator
Causal counterfactual inference: "What if Delhi implements Odd-Even tomorrow?"
"""
from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import Optional
from models.forecast import ForecastModel

router = APIRouter()
_forecast = ForecastModel()


class SimulationRequest(BaseModel):
    city: str = "Delhi"
    scenarios: list[str]  # e.g. ["odd_even_ring_road", "halt_nh48_construction"]
    hour_offset: int = 6  # How many hours from now to evaluate


SCENARIO_DEFINITIONS = {
    "odd_even_ring_road": {
        "label": "Odd-Even Rule on Ring Road",
        "description": "Restricts private vehicle traffic on Ring Road on alternate days",
        "emission_reduction": {"vehicles_pct": -40, "affected_wards": ["Dwarka", "Rohini", "Punjabi Bagh"]},
    },
    "halt_nh48_construction": {
        "label": "Halt NH-48 Construction (48 hrs)",
        "description": "Temporary halt on earthwork at the airport expansion site",
        "emission_reduction": {"construction_pct": -70, "affected_wards": ["Dwarka", "R.K. Puram"]},
    },
    "truck_ban_6pm": {
        "label": "Truck Entry Ban (6PM – 10AM)",
        "description": "Bans heavy commercial vehicles from entering Delhi 6PM–10AM",
        "emission_reduction": {"vehicles_pct": -25, "affected_wards": ["Anand Vihar", "Shahdara"]},
    },
    "badarpur_reduction_50pct": {
        "label": "Badarpur Plant at 50% Load",
        "description": "Reduces Badarpur Thermal Plant generation by 50%",
        "emission_reduction": {"industrial_pct": -50, "affected_wards": ["Okhla", "Connaught Place"]},
    },
    "sprinkler_all_sites": {
        "label": "Water Sprinklers at All Construction Sites",
        "description": "Mandatory water sprinkling on all active construction sites citywide",
        "emission_reduction": {"construction_pct": -40, "affected_wards": "all"},
    },
}


@router.get("/scenarios")
async def list_scenarios():
    """List all available policy scenarios for the simulator."""
    return {
        "scenarios": [
            {"id": k, "label": v["label"], "description": v["description"]}
            for k, v in SCENARIO_DEFINITIONS.items()
        ]
    }


@router.post("/run")
async def run_simulation(request: SimulationRequest = Body(...)):
    """
    Run counterfactual policy simulation.
    Returns: baseline AQI forecast vs. post-intervention AQI forecast for each ward.
    The difference is the 'policy impact'.
    """
    valid_scenarios = [s for s in request.scenarios if s in SCENARIO_DEFINITIONS]
    if not valid_scenarios:
        return {"error": "No valid scenarios provided", "available": list(SCENARIO_DEFINITIONS.keys())}

    result = await _forecast.run_counterfactual(
        city=request.city,
        scenarios=[SCENARIO_DEFINITIONS[s] for s in valid_scenarios],
        hour_offset=request.hour_offset,
    )

    return {
        "city": request.city,
        "scenarios_applied": [SCENARIO_DEFINITIONS[s]["label"] for s in valid_scenarios],
        "hour_offset": request.hour_offset,
        "results": result,
        "note": "Estimated impact based on emission reduction assumptions and wind dispersion modeling.",
    }
