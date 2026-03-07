"""策略基类 / Base Strategy"""

from __future__ import annotations

from abc import ABC, abstractmethod
from models.market_data import Kline
from models.signal import TradeSignal


class BaseStrategy(ABC):
    """所有交易策略的基类"""

    name: str = "base"

    @abstractmethod
    def evaluate(self, klines: list[Kline], current_position: float = 0.0) -> TradeSignal | None:
        """评估行情数据，返回交易信号或 None"""
        ...
