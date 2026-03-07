"""交易相关 API / Trading Routes"""

from __future__ import annotations

import threading
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config.settings import (
    EXCHANGE_MODE,
    EXCHANGE_NAME,
    EXCHANGE_API_KEY,
    EXCHANGE_SECRET,
    EXCHANGE_PASSWORD,
    INITIAL_CAPITAL,
    TRADING_SYMBOL,
)
from graph.workflow import build_graph
from utils.exchange_client import create_exchange_client
from utils.logger import get_logger

logger = get_logger("api.trading")
router = APIRouter()

# 运行状态
_trading_state: dict = {"running": False, "result": None, "error": None}


class StartRequest(BaseModel):
    symbol: str = TRADING_SYMBOL
    mode: str = EXCHANGE_MODE
    initial_capital: float = INITIAL_CAPITAL


@router.post("/start")
async def start_trading(req: StartRequest):
    if _trading_state["running"]:
        raise HTTPException(400, "Trading session already running")

    _trading_state["running"] = True
    _trading_state["result"] = None
    _trading_state["error"] = None

    def run():
        try:
            exchange = create_exchange_client(
                mode=req.mode,
                exchange_name=EXCHANGE_NAME,
                api_key=EXCHANGE_API_KEY,
                secret=EXCHANGE_SECRET,
                password=EXCHANGE_PASSWORD,
                initial_balance=req.initial_capital,
            )
            graph = build_graph()
            initial_state = {
                "messages": [],
                "exchange": exchange,
                "market_data": {},
                "signals": [],
                "orders": [],
                "positions": [],
                "portfolio": {
                    "total_value": req.initial_capital,
                    "cash_balance": req.initial_capital,
                    "positions": [],
                    "max_drawdown_pct": 0,
                    "peak_value": req.initial_capital,
                },
                "risk_alerts": [],
                "current_phase": "sensor",
                "iteration": 0,
            }
            result = graph.invoke(initial_state)
            # Remove non-serializable exchange client
            result.pop("exchange", None)
            _trading_state["result"] = result
        except Exception as e:
            logger.error("Trading error: %s", e)
            _trading_state["error"] = str(e)
        finally:
            _trading_state["running"] = False

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    return {"status": "started", "symbol": req.symbol, "mode": req.mode}


@router.get("/status")
async def trading_status():
    return {
        "running": _trading_state["running"],
        "has_result": _trading_state["result"] is not None,
        "error": _trading_state["error"],
    }


@router.get("/result")
async def trading_result():
    if _trading_state["running"]:
        return {"status": "running"}
    if _trading_state["error"]:
        return {"status": "error", "error": _trading_state["error"]}
    if _trading_state["result"]:
        result = _trading_state["result"]
        return {
            "status": "completed",
            "portfolio": result.get("portfolio", {}),
            "messages": result.get("messages", []),
            "iteration": result.get("iteration", 0),
        }
    return {"status": "idle"}


@router.post("/stop")
async def stop_trading():
    # Note: In a real system, we'd use a cancellation token
    _trading_state["running"] = False
    return {"status": "stopped"}
