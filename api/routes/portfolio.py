"""资产组合 API / Portfolio Routes"""

from __future__ import annotations

from fastapi import APIRouter

from config.settings import (
    EXCHANGE_MODE,
    EXCHANGE_NAME,
    EXCHANGE_API_KEY,
    EXCHANGE_SECRET,
    EXCHANGE_PASSWORD,
    INITIAL_CAPITAL,
    TRADING_SYMBOL,
)
from agents.asset_manager import AssetManager
from utils.exchange_client import create_exchange_client
from utils.logger import get_logger

logger = get_logger("api.portfolio")
router = APIRouter()


@router.get("/snapshot")
async def portfolio_snapshot():
    exchange = create_exchange_client(
        mode=EXCHANGE_MODE,
        exchange_name=EXCHANGE_NAME,
        api_key=EXCHANGE_API_KEY,
        secret=EXCHANGE_SECRET,
        password=EXCHANGE_PASSWORD,
        initial_balance=INITIAL_CAPITAL,
    )
    manager = AssetManager(exchange)
    snapshot = manager.snapshot(TRADING_SYMBOL)
    return snapshot


@router.get("/balance")
async def get_balance():
    exchange = create_exchange_client(
        mode=EXCHANGE_MODE,
        exchange_name=EXCHANGE_NAME,
        api_key=EXCHANGE_API_KEY,
        secret=EXCHANGE_SECRET,
        password=EXCHANGE_PASSWORD,
        initial_balance=INITIAL_CAPITAL,
    )
    return exchange.fetch_balance()
