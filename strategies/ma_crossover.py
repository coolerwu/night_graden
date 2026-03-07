"""均线交叉策略 / Moving Average Crossover Strategy"""

from __future__ import annotations

from models.market_data import Kline
from models.signal import TradeSignal, SignalType
from strategies.base_strategy import BaseStrategy


class MACrossoverStrategy(BaseStrategy):
    """双均线交叉策略：短期均线上穿长期均线做多，下穿做空"""

    name = "ma_crossover"

    def __init__(self, short_period: int = 5, long_period: int = 20):
        self.short_period = short_period
        self.long_period = long_period

    def _sma(self, closes: list[float], period: int) -> float:
        if len(closes) < period:
            return closes[-1]
        return sum(closes[-period:]) / period

    def evaluate(self, klines: list[Kline], current_position: float = 0.0) -> TradeSignal | None:
        if len(klines) < self.long_period + 1:
            return None

        closes = [k.close for k in klines]
        current_short = self._sma(closes, self.short_period)
        current_long = self._sma(closes, self.long_period)
        prev_short = self._sma(closes[:-1], self.short_period)
        prev_long = self._sma(closes[:-1], self.long_period)

        symbol = klines[-1].symbol
        price = klines[-1].close

        # 金叉：短均线从下方穿越长均线
        if prev_short <= prev_long and current_short > current_long:
            return TradeSignal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                price=price,
                strategy_name=self.name,
                confidence=0.7,
                reason=f"Golden cross: MA{self.short_period}={current_short:.2f} > MA{self.long_period}={current_long:.2f}",
            )

        # 死叉：短均线从上方穿越长均线
        if prev_short >= prev_long and current_short < current_long:
            if current_position > 0:
                return TradeSignal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    price=price,
                    strategy_name=self.name,
                    confidence=0.7,
                    reason=f"Death cross: MA{self.short_period}={current_short:.2f} < MA{self.long_period}={current_long:.2f}",
                )

        return None
