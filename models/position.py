"""持仓与资产模型 / Position & Portfolio Models"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class Position(BaseModel):
    """持仓 / Single position"""
    symbol: str
    quantity: float = 0.0
    avg_entry_price: float = 0.0
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def pnl_pct(self) -> float:
        if self.avg_entry_price == 0:
            return 0.0
        return (self.current_price - self.avg_entry_price) / self.avg_entry_price * 100


class PortfolioSnapshot(BaseModel):
    """资产组合快照 / Portfolio snapshot"""
    total_value: float = 0.0
    cash_balance: float = 0.0
    positions: list[Position] = Field(default_factory=list)
    total_unrealized_pnl: float = 0.0
    total_realized_pnl: float = 0.0
    max_drawdown_pct: float = 0.0
    peak_value: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
