"""Night Garden (夜花园) — 多智能体量化交易系统入口 / Entry Point"""

from __future__ import annotations

from config.settings import (
    EXCHANGE_MODE,
    EXCHANGE_NAME,
    EXCHANGE_API_KEY,
    EXCHANGE_SECRET,
    EXCHANGE_PASSWORD,
    INITIAL_CAPITAL,
    TRADING_SYMBOL,
    MAX_ITERATIONS,
)
from graph.workflow import build_graph
from utils.exchange_client import create_exchange_client
from utils.logger import get_logger

logger = get_logger("main")


def main():
    print("=" * 60)
    print("  Night Garden (夜花园) — Multi-Agent Quant System")
    print("=" * 60)

    # 创建交易所客户端
    exchange = create_exchange_client(
        mode=EXCHANGE_MODE,
        exchange_name=EXCHANGE_NAME,
        api_key=EXCHANGE_API_KEY,
        secret=EXCHANGE_SECRET,
        password=EXCHANGE_PASSWORD,
        initial_balance=INITIAL_CAPITAL,
    )

    print(f"\n  Mode:    {EXCHANGE_MODE}")
    print(f"  Symbol:  {TRADING_SYMBOL}")
    print(f"  Capital: {INITIAL_CAPITAL}")
    print(f"  Max Iterations: {MAX_ITERATIONS}")
    print("=" * 60)

    # 构建工作流
    graph = build_graph()

    # 初始状态
    initial_state = {
        "messages": [],
        "exchange": exchange,
        "market_data": {},
        "signals": [],
        "orders": [],
        "positions": [],
        "portfolio": {
            "total_value": INITIAL_CAPITAL,
            "cash_balance": INITIAL_CAPITAL,
            "positions": [],
            "max_drawdown_pct": 0,
            "peak_value": INITIAL_CAPITAL,
        },
        "risk_alerts": [],
        "current_phase": "sensor",
        "iteration": 0,
    }

    # 运行工作流
    logger.info("Starting trading workflow...")
    final_state = graph.invoke(initial_state)

    # 输出结果
    print("\n" + "=" * 60)
    print("  Trading Session Complete")
    print("=" * 60)

    portfolio = final_state.get("portfolio", {})
    print(f"\n  Final Value:  {portfolio.get('total_value', 0):.2f}")
    print(f"  PnL:          {portfolio.get('total_realized_pnl', 0):.2f}")
    print(f"  Max Drawdown: {portfolio.get('max_drawdown_pct', 0):.2f}%")
    print(f"  Iterations:   {final_state.get('iteration', 0)}")

    # 审计日志
    messages = final_state.get("messages", [])
    print(f"\n  Audit Log ({len(messages)} entries):")
    for msg in messages:
        print(f"    [{msg.get('agent', '?')}] {msg.get('type', '?')}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
