"""网格交易策略 / Grid Trading Strategy"""

from __future__ import annotations

from models.market_data import Kline
from models.signal import TradeSignal, SignalType
from strategies.base_strategy import BaseStrategy


class GridTradingStrategy(BaseStrategy):
    """网格交易：在预设价格区间内自动挂买卖单"""

    name = "grid_trading"

    def __init__(
        self,
        grid_size_pct: float = 2.0,
        num_grids: int = 5,
    ):
        self.grid_size_pct = grid_size_pct
        self.num_grids = num_grids
        self._last_grid_level: float | None = None

    def evaluate(self, klines: list[Kline], current_position: float = 0.0) -> TradeSignal | None:
        if len(klines) < 2:
            return None

        price = klines[-1].close
        symbol = klines[-1].symbol

        # 初始化网格基准
        if self._last_grid_level is None:
            self._last_grid_level = price
            return None

        grid_step = self._last_grid_level * self.grid_size_pct / 100

        # 价格下穿一个网格 → 买入
        if price <= self._last_grid_level - grid_step:
            self._last_grid_level = price
            return TradeSignal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                price=price,
                strategy_name=self.name,
                confidence=0.6,
                reason=f"Grid buy: price dropped to {price:.2f}, grid step={grid_step:.2f}",
            )

        # 价格上穿一个网格 → 卖出（需要有持仓）
        if price >= self._last_grid_level + grid_step and current_position > 0:
            self._last_grid_level = price
            return TradeSignal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                price=price,
                strategy_name=self.name,
                confidence=0.6,
                reason=f"Grid sell: price rose to {price:.2f}, grid step={grid_step:.2f}",
            )

        return None
