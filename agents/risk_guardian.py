"""风控守卫 Agent / Risk Guardian Agent

职责：在交易执行前做预检，检查风控规则，拦截高风险交易。
纯代码逻辑驱动，确保风控判断的实时性和可靠性。
"""

from __future__ import annotations

from typing import Any

from config.settings import MAX_POSITION_SIZE, MAX_DRAWDOWN_PCT
from models.signal import SignalType
from utils.logger import get_logger

logger = get_logger("risk_guardian")


class RiskGuardian:
    """风控守卫：检查信号是否满足风控规则"""

    def __init__(
        self,
        max_position_size: float = MAX_POSITION_SIZE,
        max_drawdown_pct: float = MAX_DRAWDOWN_PCT,
        max_single_order_pct: float = 30.0,
    ):
        self.max_position_size = max_position_size
        self.max_drawdown_pct = max_drawdown_pct
        self.max_single_order_pct = max_single_order_pct

    def check_signals(
        self,
        signals: list[dict],
        portfolio: dict,
        positions: list[dict],
    ) -> tuple[list[dict], list[str]]:
        """
        检查信号列表，返回 (通过的信号, 风控告警列表)
        """
        approved = []
        alerts = []

        # 检查整体回撤
        drawdown = portfolio.get("max_drawdown_pct", 0)
        if drawdown >= self.max_drawdown_pct:
            alerts.append(
                f"HALT: Max drawdown {drawdown:.1f}% >= limit {self.max_drawdown_pct}%. "
                "All buy signals blocked."
            )
            # 只允许卖出信号
            for s in signals:
                if s.get("signal_type") == SignalType.SELL.value:
                    approved.append(s)
            return approved, alerts

        current_qty = sum(p.get("quantity", 0) for p in positions)

        for signal in signals:
            signal_alerts = self._check_single_signal(signal, current_qty, portfolio)
            if signal_alerts:
                alerts.extend(signal_alerts)
                logger.warning("[risk_guardian] Signal blocked: %s", signal_alerts)
            else:
                approved.append(signal)
                if signal.get("signal_type") == SignalType.BUY.value:
                    current_qty += signal.get("quantity", 0)

        return approved, alerts

    def _check_single_signal(
        self, signal: dict, current_qty: float, portfolio: dict
    ) -> list[str]:
        issues = []
        qty = signal.get("quantity", 0)

        # 仓位上限检查
        if signal.get("signal_type") == SignalType.BUY.value:
            if current_qty + qty > self.max_position_size:
                issues.append(
                    f"Position limit: {current_qty + qty:.6f} > max {self.max_position_size}"
                )

            # 单笔占比检查
            total_value = portfolio.get("total_value", 0)
            if total_value > 0:
                order_value = qty * signal.get("price", 0)
                order_pct = order_value / total_value * 100
                if order_pct > self.max_single_order_pct:
                    issues.append(
                        f"Single order too large: {order_pct:.1f}% > max {self.max_single_order_pct}%"
                    )

        # 卖出不能超过持仓
        if signal.get("signal_type") == SignalType.SELL.value:
            if qty > current_qty:
                issues.append(f"Cannot sell {qty:.6f}, only hold {current_qty:.6f}")

        return issues


def risk_guardian_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node function"""
    signals = state.get("signals", [])
    portfolio = state.get("portfolio", {})
    positions = state.get("positions", [])

    guardian = RiskGuardian()
    approved_signals, alerts = guardian.check_signals(signals, portfolio, positions)

    logger.info(
        "[risk_guardian] %d/%d signals approved, %d alerts",
        len(approved_signals),
        len(signals),
        len(alerts),
    )

    return {
        "signals": approved_signals,
        "risk_alerts": alerts,
        "current_phase": "execute" if approved_signals else "asset",
        "messages": [
            {
                "agent": "risk_guardian",
                "type": "risk_check",
                "data": {
                    "approved": len(approved_signals),
                    "blocked": len(signals) - len(approved_signals),
                    "alerts": alerts,
                },
            }
        ],
    }
