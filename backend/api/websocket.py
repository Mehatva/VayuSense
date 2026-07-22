"""
WebSocket — Live AQI + Economic Counter + IoT Sensor Spikes
Broadcasts real-time data to all connected dashboard clients.
"""
import asyncio
import json
import logging
import random
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from models.economic import EconomicCalculator

router = APIRouter()
logger = logging.getLogger(__name__)
_calc = EconomicCalculator()

# Mock Wards for IoT Simulation
SIM_WARDS = ["Dwarka", "Okhla", "Anand Vihar", "Rohini", "Connaught Place", "Shahdara", "R.K. Puram"]
SIM_CAUSES = [
    "Suspected industrial emissions",
    "Heavy vehicular congestion",
    "Localized waste burning detected",
    "Construction dust anomaly",
    "Stagnant dispersion / low wind",
]

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []
        self._iot_task = None

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.info(f"WS connected. Total: {len(self.active)}")
        
        # Start the global IoT simulator loop if it's not running
        if self._iot_task is None:
            self._iot_task = asyncio.create_task(self._simulate_iot_stream())

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)
        logger.info(f"WS disconnected. Total: {len(self.active)}")

    async def broadcast(self, data: dict):
        if not self.active:
            return
        dead = []
        message = json.dumps(data)
        for ws in self.active:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def _simulate_iot_stream(self):
        """Background loop broadcasting simulated high-frequency IoT events."""
        logger.info("Started IoT Sensor Simulator Stream")
        while True:
            # Fire an event every 10 to 18 seconds to feel organic
            await asyncio.sleep(random.randint(10, 18))
            
            if not self.active:
                continue # Pause simulation if no clients
                
            ward = random.choice(SIM_WARDS)
            pm25_spike = random.randint(25, 120)
            cause = random.choice(SIM_CAUSES)
            
            event = {
                "type": "iot_spike",
                "data": {
                    "id": f"evt_{random.randint(1000, 9999)}",
                    "ward": ward,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metric": "PM2.5",
                    "delta": f"+{pm25_spike}",
                    "severity": "high" if pm25_spike > 80 else "medium",
                    "cause": cause
                }
            }
            await self.broadcast(event)


manager = ConnectionManager()


@router.websocket("/live-updates")
async def websocket_live_updates(ws: WebSocket, city: str = "Delhi"):
    """
    WebSocket endpoint for real-time dashboard updates.
    Broadcasts every 60 seconds:
      - Economic damage tick
    Plus asynchronous IoT spikes driven by the ConnectionManager.
    """
    await manager.connect(ws)
    try:
        while True:
            # The client-specific loop handles the slow economic tick
            tick = await _calc.get_tick(city=city)
            await ws.send_text(json.dumps({
                "type": "economic_tick",
                "data": tick,
            }))
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(ws)
