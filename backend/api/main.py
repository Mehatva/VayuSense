"""
VayuSense — FastAPI Main Application
Central entry point with CORS, routes, WebSocket, and scheduler.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from api.routes import aqi, attribution, forecast, enforcement, citizen, economic, simulator
from api.websocket import router as ws_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    logger.info(f"🌬️  VayuSense v{settings.app_version} starting up...")
    logger.info(f"   Environment : {settings.app_env}")
    logger.info(f"   Primary City: {settings.primary_city}")

    # Start background data refresh scheduler
    from core.scheduler import start_scheduler
    scheduler = await start_scheduler()

    yield

    # Shutdown
    logger.info("VayuSense shutting down...")
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="VayuSense API",
    description=(
        "AI-Powered Urban Air Quality Intelligence Platform. "
        "Real-time AQI attribution, forecasting, enforcement intelligence, "
        "and multilingual citizen advisories for Indian cities."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────────────────
app.include_router(aqi.router,         prefix="/api/aqi",         tags=["AQI"])
app.include_router(attribution.router, prefix="/api/attribution", tags=["Attribution"])
app.include_router(forecast.router,    prefix="/api/forecast",    tags=["Forecast"])
app.include_router(enforcement.router, prefix="/api/enforcement", tags=["Enforcement"])
app.include_router(citizen.router,     prefix="/api/citizen",     tags=["Citizen"])
app.include_router(economic.router,    prefix="/api/economic",    tags=["Economic"])
app.include_router(simulator.router,   prefix="/api/simulator",   tags=["Simulator"])
app.include_router(ws_router,          prefix="/ws",              tags=["WebSocket"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "VayuSense",
        "version": settings.app_version,
        "status": "operational",
        "tagline": "India breathes. VayuSense acts.",
        "cities_active": list(settings.cities.keys()),
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "environment": settings.app_env}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.app_env == "development",
        log_level="info",
    )
