"""市场数据模型 / Market Data Models"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class Kline(BaseModel):
    """K线数据 / Candlestick data"""
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def mid(self) -> float:
        return (self.high + self.low) / 2


class TickerSnapshot(BaseModel):
    """实时行情快照 / Real-time ticker snapshot"""
    symbol: str
    last_price: float
    bid: float
    ask: float
    volume_24h: float
    change_pct_24h: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OrderBookSnapshot(BaseModel):
    """订单簿快照 / Order book snapshot"""
    symbol: str
    bids: list[list[float]] = Field(default_factory=list)  # [[price, qty], ...]
    asks: list[list[float]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def spread(self) -> float:
        if self.asks and self.bids:
            return self.asks[0][0] - self.bids[0][0]
        return 0.0
