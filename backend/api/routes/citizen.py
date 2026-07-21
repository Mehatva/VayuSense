"""
Citizen Advisory Routes
Generates multilingual health advisories and handles WhatsApp alerts.
"""
from fastapi import APIRouter, Query, Body
from pydantic import BaseModel
from models.citizen_advisory import CitizenAdvisoryAgent

router = APIRouter()
_agent = CitizenAdvisoryAgent()

SUPPORTED_LANGUAGES = [
    "Hindi", "Bengali", "Telugu", "Marathi", "Tamil",
    "Kannada", "Gujarati", "Malayalam", "Punjabi",
    "Odia", "Assamese", "Urdu"
]


class AlertRequest(BaseModel):
    city: str = "Delhi"
    ward: str = "Dwarka"
    language: str = "Hindi"
    channel: str = "whatsapp"  # whatsapp | sms | push


@router.get("/advisory")
async def get_advisory(
    city: str = Query(default="Delhi"),
    ward: str = Query(default="Dwarka"),
    language: str = Query(default="Hindi"),
):
    """
    Generate a health advisory for a specific ward in the requested language.
    Uses Gemini API for natural language generation.
    Supports 12 Indian languages.
    """
    if language not in SUPPORTED_LANGUAGES:
        language = "Hindi"

    return await _agent.generate_advisory(
        city=city,
        ward=ward,
        language=language,
    )


@router.post("/send-alert")
async def send_citizen_alert(request: AlertRequest):
    """
    Send a health advisory via WhatsApp/SMS to subscribers in a ward.
    Demo: sends to configured Twilio sandbox number.
    """
    advisory = await _agent.generate_advisory(
        city=request.city,
        ward=request.ward,
        language=request.language,
    )
    result = await _agent.send_via_channel(
        message=advisory["message"],
        channel=request.channel,
    )
    return {"advisory": advisory, "delivery": result}


@router.get("/languages")
async def get_supported_languages():
    """List all supported languages for citizen advisories."""
    return {"languages": SUPPORTED_LANGUAGES, "count": len(SUPPORTED_LANGUAGES)}
