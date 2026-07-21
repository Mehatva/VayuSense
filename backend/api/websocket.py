"""
WebSocket — Live AQI + Economic Counter Updates
Broadcasts real-time data to all connected dashboard clients.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from models.economic import EconomicCalculator

router = APIRouter()
logger = logging.getLogger(__name__)
_calc = EconomicCalculator()


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.info(f"WS connected. Total: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
        logger.info(f"WS disconnected. Total: {len(self.active)}")

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)


manager = ConnectionManager()


@router.websocket("/live-updates")
async def websocket_live_updates(ws: WebSocket, city: str = "Delhi"):
    """
    WebSocket endpoint for real-time dashboard updates.
    Broadcasts every 60 seconds:
      - Economic damage tick
      - City AQI summary
    """
    await manager.connect(ws)
    try:
        while True:
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
