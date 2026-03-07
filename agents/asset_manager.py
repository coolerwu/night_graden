"""资产管家 Agent / Asset Manager Agent

职责：跟踪账户余额、持仓分布、盈亏统计，生成资产报告。
LLM 辅助：用 LLM 生成资产分析报告和组合调整建议。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from agents.base import BaseAgent
from config.prompts import ASSET_MANAGER_PROMPT
from config.settings import INITIAL_CAPITAL
from utils.exchange_client import BaseExchangeClient
from utils.logger import get_logger

logger = get_logger("asset_manager")


class AssetManager(BaseAgent):
    """资产管家：统计持仓、计算盈亏、生成报告"""

    def __init__(self, exchange: BaseExchangeClient):
        super().__init__(name="asset_manager", system_prompt=ASSET_MANAGER_PROMPT)
        self.exchange = exchange
        self._peak_value = INITIAL_CAPITAL

    def snapshot(self, symbol: str = "BTC/USDT") -> dict:
        balance = self.exchange.fetch_balance()
        ticker = self.exchange.fetch_ticker(symbol)

        base_currency = symbol.split("/")[0]
        quote_currency = symbol.split("/")[1]

        base_qty = balance.get(base_currency, 0)
        quote_qty = balance.get(quote_currency, 0)
        price = ticker.last_price

        position_value = base_qty * price
        total_value = quote_qty + position_value

        # 更新峰值 & 回撤
        if total_value > self._peak_value:
            self._peak_value = total_value
        drawdown_pct = (
            (self._peak_value - total_value) / self._peak_value * 100
            if self._peak_value > 0
            else 0
        )

        positions = []
        if base_qty > 0:
            positions.append(
                {
                    "symbol": symbol,
                    "quantity": base_qty,
                    "current_price": price,
                    "avg_entry_price": 0,
                    "unrealized_pnl": 0,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )

        portfolio = {
            "total_value": round(total_value, 2),
            "cash_balance": round(quote_qty, 2),
            "positions": positions,
            "total_unrealized_pnl": round(position_value - (base_qty * price), 2),
            "total_realized_pnl": round(total_value - INITIAL_CAPITAL, 2),
            "max_drawdown_pct": round(drawdown_pct, 2),
            "peak_value": round(self._peak_value, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }

        return portfolio

    def generate_report(self, portfolio: dict) -> dict:
        """使用 LLM 生成资产分析报告"""
        prompt = (
            f"当前资产状态:\n{portfolio}\n"
            f"初始资金: {INITIAL_CAPITAL}\n"
            "请分析资产状况并给出建议，输出 JSON。"
        )
        try:
            text = self.invoke_llm(prompt)
            return self.parse_json_response(text)
        except Exception as e:
            logger.warning("LLM report failed, using basic report: %s", e)
            pnl = portfolio.get("total_realized_pnl", 0)
            return {
                "total_value": portfolio.get("total_value", 0),
                "risk_score": min(10, max(1, int(portfolio.get("max_drawdown_pct", 0)))),
                "suggestions": ["继续观察" if pnl >= 0 else "考虑减仓控制风险"],
                "summary": f"总资产 {portfolio.get('total_value', 0)}, PnL: {pnl:.2f}",
            }


def asset_manager_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node function"""
    exchange = state["exchange"]
    symbol = state.get("market_data", {}).get("symbol", "BTC/USDT")

    manager = AssetManager(exchange)
    portfolio = manager.snapshot(symbol)
    report = manager.generate_report(portfolio)

    iteration = state.get("iteration", 0) + 1

    logger.info(
        "[asset_manager] Total: %.2f, Drawdown: %.2f%%, Iter: %d",
        portfolio["total_value"],
        portfolio["max_drawdown_pct"],
        iteration,
    )

    return {
        "portfolio": portfolio,
        "positions": portfolio["positions"],
        "iteration": iteration,
        "current_phase": "sensor",
        "messages": [
            {
                "agent": "asset_manager",
                "type": "portfolio_update",
                "data": {"portfolio": portfolio, "report": report},
            }
        ],
    }
