"""交易工作流状态 / Trading Workflow State"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class TradingState(TypedDict):
    """LangGraph 工作流状态定义"""

    # 审计日志（append-only）
    messages: Annotated[list[dict], operator.add]

    # 交易所客户端（不序列化）
    exchange: Any

    # 市场数据
    market_data: dict

    # 交易信号（经策略引擎生成，经风控过滤）
    signals: list[dict]

    # 已执行订单
    orders: list[dict]

    # 当前持仓
    positions: list[dict]

    # 资产组合快照
    portfolio: dict

    # 风控告警
    risk_alerts: list[str]

    # 当前阶段
    current_phase: str

    # 循环计数
    iteration: int
