"""FastAPI 服务端 / API Server with WebSocket Support"""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes.trading import router as trading_router
from api.routes.portfolio import router as portfolio_router
from utils.logger import get_logger

logger = get_logger("api_server")


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        data = json.dumps(message, default=str)
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                pass


ws_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Night Garden API server starting...")
    yield
    logger.info("Night Garden API server shutting down...")


app = FastAPI(
    title="Night Garden (夜花园)",
    description="Multi-Agent Quantitative Trading System API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trading_router, prefix="/api/trading", tags=["Trading"])
app.include_router(portfolio_router, prefix="/api/portfolio", tags=["Portfolio"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            logger.info("WS received: %s", msg.get("type", "unknown"))
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
