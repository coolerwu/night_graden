"""市场感知器 Agent / Market Sensor Agent

职责：采集行情数据，分析市场状态，推送给后续 Agent。
LLM 辅助：用 LLM 生成市场趋势分析摘要。
"""

from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from config.prompts import MARKET_SENSOR_PROMPT
from config.settings import TRADING_SYMBOL, TRADING_TIMEFRAME
from utils.exchange_client import BaseExchangeClient
from utils.logger import get_logger

logger = get_logger("market_sensor")


class MarketSensor(BaseAgent):
    def __init__(self, exchange: BaseExchangeClient):
        super().__init__(name="market_sensor", system_prompt=MARKET_SENSOR_PROMPT)
        self.exchange = exchange

    def collect(self, symbol: str | None = None, timeframe: str | None = None) -> dict:
        symbol = symbol or TRADING_SYMBOL
        timeframe = timeframe or TRADING_TIMEFRAME

        klines = self.exchange.fetch_klines(symbol, timeframe, limit=50)
        ticker = self.exchange.fetch_ticker(symbol)

        klines_data = [k.model_dump() for k in klines[-20:]]
        ticker_data = ticker.model_dump()

        # 用 LLM 分析市场趋势
        prompt = (
            f"Symbol: {symbol}\n"
            f"Ticker: {ticker_data}\n"
            f"Recent 20 Klines (OHLCV): {klines_data}\n"
            "请分析市场趋势并输出 JSON。"
        )
        try:
            analysis_text = self.invoke_llm(prompt)
            analysis = self.parse_json_response(analysis_text)
        except Exception as e:
            logger.warning("LLM analysis failed, using rule-based fallback: %s", e)
            analysis = self._rule_based_analysis(klines)

        return {
            "symbol": symbol,
            "ticker": ticker_data,
            "klines_count": len(klines),
            "analysis": analysis,
        }

    def _rule_based_analysis(self, klines) -> dict:
        if len(klines) < 5:
            return {"trend": "sideways", "volatility": "low", "summary": "数据不足"}

        closes = [k.close for k in klines[-20:]]
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes) / len(closes)

        trend = "bullish" if ma5 > ma20 else "bearish" if ma5 < ma20 else "sideways"
        high = max(k.high for k in klines[-20:])
        low = min(k.low for k in klines[-20:])
        volatility_pct = (high - low) / low * 100

        if volatility_pct > 5:
            vol = "high"
        elif volatility_pct > 2:
            vol = "medium"
        else:
            vol = "low"

        return {
            "trend": trend,
            "volatility": vol,
            "key_levels": {"support": round(low, 2), "resistance": round(high, 2)},
            "summary": f"MA5={round(ma5,2)}, MA20={round(ma20,2)}, trend={trend}",
        }


def market_sensor_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node function"""
    exchange = state["exchange"]
    sensor = MarketSensor(exchange)
    market_data = sensor.collect()

    logger.info(
        "[market_sensor] %s trend=%s",
        market_data["symbol"],
        market_data["analysis"].get("trend", "unknown"),
    )

    return {
        "market_data": market_data,
        "current_phase": "strategy",
        "messages": [
            {
                "agent": "market_sensor",
                "type": "market_update",
                "data": market_data["analysis"],
            }
        ],
    }
