"""工作流编排 / Workflow Graph Construction"""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from agents.market_sensor import market_sensor_node
from agents.strategy_engine import strategy_engine_node
from agents.risk_guardian import risk_guardian_node
from agents.trade_executor import trade_executor_node
from agents.asset_manager import asset_manager_node
from config.settings import MAX_ITERATIONS
from graph.state import TradingState
from utils.logger import get_logger

logger = get_logger("workflow")


def route_after_risk(state: TradingState) -> str:
    """风控后路由：有通过的信号则执行，否则跳到资产管理"""
    signals = state.get("signals", [])
    if signals:
        return "trade_executor"
    logger.info("[workflow] No approved signals, skipping to asset_manager")
    return "asset_manager"


def route_after_asset(state: TradingState) -> str:
    """资产管理后路由：检查是否继续循环"""
    iteration = state.get("iteration", 0)
    if iteration >= MAX_ITERATIONS:
        logger.info("[workflow] Max iterations (%d) reached, ending", MAX_ITERATIONS)
        return END

    # 检查是否有严重风控告警需要停止
    alerts = state.get("risk_alerts", [])
    for alert in alerts:
        if "HALT" in alert:
            logger.info("[workflow] HALT alert detected, ending")
            return END

    return "market_sensor"


def build_graph() -> StateGraph:
    """构建并编译交易工作流图"""
    graph = StateGraph(TradingState)

    # 添加节点
    graph.add_node("market_sensor", market_sensor_node)
    graph.add_node("strategy_engine", strategy_engine_node)
    graph.add_node("risk_guardian", risk_guardian_node)
    graph.add_node("trade_executor", trade_executor_node)
    graph.add_node("asset_manager", asset_manager_node)

    # 设置入口
    graph.set_entry_point("market_sensor")

    # 固定边
    graph.add_edge("market_sensor", "strategy_engine")
    graph.add_edge("strategy_engine", "risk_guardian")
    graph.add_edge("trade_executor", "asset_manager")

    # 条件边
    graph.add_conditional_edges(
        "risk_guardian",
        route_after_risk,
        {"trade_executor": "trade_executor", "asset_manager": "asset_manager"},
    )
    graph.add_conditional_edges(
        "asset_manager",
        route_after_asset,
        {"market_sensor": "market_sensor", END: END},
    )

    return graph.compile()
