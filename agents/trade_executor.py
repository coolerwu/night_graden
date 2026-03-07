"""交易执行器 Agent / Trade Executor Agent

职责：接收经风控审批的交易信号，通过交易所 API 执行下单。
纯代码逻辑驱动，确保订单执行的确定性。
"""

from __future__ import annotations

from typing import Any

from models.order import OrderSide, OrderType, OrderStatus
from models.signal import SignalType
from utils.exchange_client import BaseExchangeClient
from utils.logger import get_logger

logger = get_logger("trade_executor")


class TradeExecutor:
    """交易执行器：将信号转为实际订单"""

    def __init__(self, exchange: BaseExchangeClient):
        self.exchange = exchange

    def execute_signals(self, signals: list[dict]) -> list[dict]:
        """执行一批交易信号，返回订单结果列表"""
        orders = []
        for signal in signals:
            order = self._execute_single(signal)
            if order:
                orders.append(order)
        return orders

    def _execute_single(self, signal: dict) -> dict | None:
        symbol = signal.get("symbol", "")
        signal_type = signal.get("signal_type", "")
        quantity = signal.get("quantity", 0)
        price = signal.get("price", 0)

        if not symbol or not quantity:
            logger.warning("Invalid signal, skipping: %s", signal)
            return None

        side = OrderSide.BUY if signal_type == SignalType.BUY.value else OrderSide.SELL

        try:
            order = self.exchange.place_order(
                symbol=symbol,
                side=side,
                order_type=OrderType.MARKET,
                quantity=quantity,
                price=price,
            )

            result = order.model_dump()
            if order.status == OrderStatus.FILLED:
                logger.info(
                    "[trade_executor] Filled: %s %s %.6f @ %.2f",
                    side.value,
                    symbol,
                    order.filled_quantity,
                    order.filled_price,
                )
            else:
                logger.warning(
                    "[trade_executor] Order %s: %s", order.status.value, result
                )

            return result
        except Exception as e:
            logger.error("[trade_executor] Execution error: %s", e)
            return {
                "symbol": symbol,
                "side": side.value,
                "quantity": quantity,
                "status": "failed",
                "error": str(e),
            }


def trade_executor_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node function"""
    exchange = state["exchange"]
    signals = state.get("signals", [])

    if not signals:
        logger.info("[trade_executor] No signals to execute")
        return {
            "current_phase": "asset",
            "messages": [
                {"agent": "trade_executor", "type": "no_action", "data": {}}
            ],
        }

    executor = TradeExecutor(exchange)
    orders = executor.execute_signals(signals)

    logger.info("[trade_executor] Executed %d orders", len(orders))

    return {
        "orders": orders,
        "current_phase": "asset",
        "messages": [
            {
                "agent": "trade_executor",
                "type": "orders",
                "data": {"count": len(orders), "orders": orders},
            }
        ],
    }
