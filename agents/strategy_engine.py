"""策略引擎 Agent / Strategy Engine Agent

职责：加载策略模块，基于行情数据生成交易信号。
纯代码逻辑驱动（不使用 LLM），确保信号生成的确定性和速度。
"""

from __future__ import annotations

from typing import Any

from config.settings import TRADING_SYMBOL, TRADING_TIMEFRAME, MAX_POSITION_SIZE
from models.signal import TradeSignal, SignalType
from strategies.base_strategy import BaseStrategy
from strategies.ma_crossover import MACrossoverStrategy
from strategies.grid_trading import GridTradingStrategy
from utils.exchange_client import BaseExchangeClient
from utils.logger import get_logger

logger = get_logger("strategy_engine")

# 默认策略注册表
DEFAULT_STRATEGIES: list[BaseStrategy] = [
    MACrossoverStrategy(short_period=5, long_period=20),
    GridTradingStrategy(grid_size_pct=2.0),
]


class StrategyEngine:
    """策略引擎：运行多个策略，汇总信号"""

    def __init__(
        self,
        exchange: BaseExchangeClient,
        strategies: list[BaseStrategy] | None = None,
    ):
        self.exchange = exchange
        self.strategies = strategies or DEFAULT_STRATEGIES

    def generate_signals(
        self,
        symbol: str | None = None,
        timeframe: str | None = None,
        current_position: float = 0.0,
    ) -> list[TradeSignal]:
        symbol = symbol or TRADING_SYMBOL
        timeframe = timeframe or TRADING_TIMEFRAME

        klines = self.exchange.fetch_klines(symbol, timeframe, limit=50)
        signals: list[TradeSignal] = []

        for strategy in self.strategies:
            try:
                signal = strategy.evaluate(klines, current_position)
                if signal and signal.signal_type != SignalType.HOLD:
                    # 设置默认数量
                    if signal.quantity <= 0:
                        signal.quantity = self._calc_quantity(signal, current_position)
                    signals.append(signal)
                    logger.info(
                        "[%s] Signal: %s %s @ %.2f (confidence=%.2f)",
                        strategy.name,
                        signal.signal_type.value,
                        symbol,
                        signal.price,
                        signal.confidence,
                    )
            except Exception as e:
                logger.error("[%s] Strategy error: %s", strategy.name, e)

        return signals

    def _calc_quantity(self, signal: TradeSignal, current_position: float) -> float:
        if signal.signal_type == SignalType.SELL:
            # 卖出量不能超过当前持仓
            return current_position if current_position > 0 else 0
        # 买入量：基于可用仓位计算，不超过最大仓位
        remaining = max(0, MAX_POSITION_SIZE - current_position)
        return min(0.01, remaining)


def strategy_engine_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node function"""
    exchange = state["exchange"]
    positions = state.get("positions", [])
    current_position = sum(p.get("quantity", 0) for p in positions)

    engine = StrategyEngine(exchange)
    signals = engine.generate_signals(current_position=current_position)

    signals_data = [s.model_dump() for s in signals]
    logger.info("[strategy_engine] Generated %d signals", len(signals))

    return {
        "signals": signals_data,
        "current_phase": "risk_check",
        "messages": [
            {
                "agent": "strategy_engine",
                "type": "signals",
                "data": {"count": len(signals), "signals": signals_data},
            }
        ],
    }
