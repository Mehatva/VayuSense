"""
Citizen Advisory Agent
Generates multilingual health advisories using Google Gemini API.
Supports 12 Indian languages.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

LANGUAGE_CODES = {
    "Hindi": "hi", "Bengali": "bn", "Telugu": "te", "Marathi": "mr",
    "Tamil": "ta", "Kannada": "kn", "Gujarati": "gu", "Malayalam": "ml",
    "Punjabi": "pa", "Odia": "or", "Assamese": "as", "Urdu": "ur",
}

# Fallback templates for demo (if Gemini API key not available)
FALLBACK_TEMPLATES = {
    "Hindi": {
        "Good":        "✅ {ward} में आज की हवा साफ है। बाहर निकलना सुरक्षित है।",
        "Moderate":    "🟡 {ward} में वायु गुणवत्ता मध्यम है। संवेदनशील लोग सावधानी बरतें।",
        "Poor":        "🟠 ⚠️ {ward} में आज वायु प्रदूषण अधिक है। बच्चों और बुजुर्गों को घर के अंदर रहना चाहिए।",
        "Very Poor":   "🔴 ⚠️ {ward} में वायु गुणवत्ता बहुत खराब है। बाहर जाने से बचें। N95 मास्क पहनें।",
        "Severe":      "🚨 {ward} में वायु गुणवत्ता अत्यंत खतरनाक है। कृपया घर के अंदर रहें और खिड़कियाँ बंद रखें।",
    },
    "English": {
        "Good":        "✅ Air quality in {ward} is good today. Safe for outdoor activities.",
        "Moderate":    "🟡 Air quality in {ward} is moderate. Sensitive groups should limit outdoor exertion.",
        "Poor":        "🟠 ⚠️ Unhealthy air in {ward} today. Children and elderly should stay indoors.",
        "Very Poor":   "🔴 ⚠️ Very poor air quality in {ward}. Avoid outdoor activities. Wear N95 mask.",
        "Severe":      "🚨 Hazardous air in {ward}. Stay indoors. Keep windows closed. Avoid all outdoor activity.",
    },
    "Tamil": {
        "Poor":        "🟠 ⚠️ {ward} பகுதியில் இன்று காற்று மாசுபட்டுள்ளது. குழந்தைகளை வெளியே அனுப்பாதீர்கள்.",
        "Very Poor":   "🔴 ⚠️ {ward} பகுதியில் காற்று மிகவும் மோசமாக உள்ளது. வெளியே போவதை தவிர்க்கவும்.",
    },
    "Kannada": {
        "Poor":        "🟠 ⚠️ {ward}ದಲ್ಲಿ ಇಂದು ವಾಯು ಮಾಲಿನ್ಯ ಹೆಚ್ಚಾಗಿದೆ. ಮಕ್ಕಳನ್ನು ಹೊರಗೆ ಕಳುಹಿಸಬೇಡಿ.",
        "Very Poor":   "🔴 ⚠️ {ward}ದಲ್ಲಿ ವಾಯು ಗುಣಮಟ್ಟ ತೀವ್ರ ಅಪಾಯಕಾರಿ ಮಟ್ಟದಲ್ಲಿದೆ. ಮನೆಯಲ್ಲೇ ಇರಿ.",
    },
    "Bengali": {
        "Poor":        "🟠 ⚠️ {ward}-এ আজ বায়ু দূষণ বেশি। শিশু ও বয়স্কদের বাড়িতে থাকা উচিত।",
        "Very Poor":   "🔴 ⚠️ {ward}-এ বায়ুর মান অত্যন্ত খারাপ। বাইরে বের হবেন না।",
    },
}


class CitizenAdvisoryAgent:
    def __init__(self):
        self._gemini = None
        self._init_gemini()

    def _init_gemini(self):
        try:
            import google.generativeai as genai
            if settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here":
                genai.configure(api_key=settings.gemini_api_key)
                self._gemini = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("Gemini API connected for citizen advisories")
            else:
                logger.warning("Gemini API key not set — using fallback templates")
        except Exception as e:
            logger.warning(f"Gemini init failed: {e}")

    async def generate_advisory(
        self,
        city: str,
        ward: str,
        language: str = "Hindi",
        aqi: Optional[int] = None,
        forecast_aqi: Optional[int] = None,
        category: Optional[str] = None,
    ) -> dict:
        # Use provided AQI or simulate based on ward
        if aqi is None:
            from models.forecast import WARD_BASE_AQI
            aqi = WARD_BASE_AQI.get(ward, 250)

        if category is None:
            from data.fetchers.openaq_fetcher import get_aqi_category
            category = get_aqi_category(aqi)

        if forecast_aqi is None:
            forecast_aqi = int(aqi * 1.15)  # Slightly worse tomorrow

        if self._gemini:
            message = await self._generate_with_gemini(
                city=city, ward=ward, language=language,
                aqi=aqi, forecast_aqi=forecast_aqi, category=category
            )
        else:
            message = self._generate_from_template(ward, language, category)

        return {
            "city": city,
            "ward": ward,
            "language": language,
            "language_code": LANGUAGE_CODES.get(language, "hi"),
            "current_aqi": aqi,
            "aqi_category": category,
            "forecast_aqi_6am": forecast_aqi,
            "message": message,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "powered_by": "Google Gemini" if self._gemini else "Template Engine",
        }

    async def _generate_with_gemini(
        self, city, ward, language, aqi, forecast_aqi, category
    ) -> str:
        prompt = f"""You are a public health communication expert for India's Ministry of Environment.
Generate a clear, actionable air quality health advisory in {language} for residents of {ward}, {city}.

Current AQI: {aqi} ({category})
Forecast AQI at 6AM tomorrow: {forecast_aqi}
Language required: {language} (write ONLY in {language} script, not English)

Requirements:
- Maximum 3 sentences
- One specific, actionable recommendation
- Appropriate warning emoji at the start
- Natural, conversational tone suitable for WhatsApp
- No technical jargon — write for a general audience
- If forecast is worse than current, mention to prepare tonight

Write ONLY the advisory message, nothing else."""

        try:
            response = await self._gemini.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return self._generate_from_template(ward, language, category)

    def _generate_from_template(self, ward: str, language: str, category: str) -> str:
        lang_templates = FALLBACK_TEMPLATES.get(
            language,
            FALLBACK_TEMPLATES.get("Hindi", {})
        )
        template = lang_templates.get(
            category,
            lang_templates.get("Poor", f"⚠️ Air quality advisory for {ward}. Please take precautions.")
        )
        return template.format(ward=ward)

    async def send_via_channel(self, message: str, channel: str) -> dict:
        """Send advisory via WhatsApp/SMS. Demo uses Twilio sandbox."""
        if channel == "whatsapp":
            return await self._send_whatsapp(message)
        return {"status": "simulated", "channel": channel, "message_preview": message[:100]}

    async def _send_whatsapp(self, message: str) -> dict:
        try:
            from twilio.rest import Client
            if not settings.twilio_account_sid or settings.twilio_account_sid == "your_twilio_sid":
                return {"status": "demo_mode", "note": "Add Twilio credentials to .env to send real messages"}

            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            msg = client.messages.create(
                body=message,
                from_=settings.twilio_whatsapp_from,
                to="whatsapp:+919999999999"  # Demo recipient
            )
            return {"status": "sent", "sid": msg.sid}
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return {"status": "failed", "error": str(e)}
