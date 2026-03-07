"""日志监控 Agent / Log Monitor Agent

职责：监控 production/logs/ 目录，分析日志是否有异常。
LLM 驱动。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agents.base import BaseAgent
from config.prompts import LOG_MONITOR_PROMPT
from utils.logger import get_logger
from utils.workspace import WorkspaceManager

logger = get_logger("log_monitor")


class LogMonitor(BaseAgent):
    def __init__(self, workspace: WorkspaceManager):
        super().__init__(name="log_monitor", system_prompt=LOG_MONITOR_PROMPT)
        self.workspace = workspace

    def check_logs(self) -> dict:
        """读取最新日志，分析是否有异常"""
        log_dir = self.workspace.get_log_dir()
        log_files = sorted(log_dir.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)

        if not log_files:
            return {
                "status": "healthy",
                "alert": "",
                "details": "No log files found",
                "action_required": "",
            }

        # 读取最近的日志
        recent_logs = []
        for log_file in log_files[:5]:
            content = log_file.read_text(encoding="utf-8")
            recent_logs.append(f"--- {log_file.name} ---\n{content}")

        combined = "\n\n".join(recent_logs)

        # LLM 分析
        try:
            response = self.invoke_llm(
                f"请分析以下日志：\n\n{combined[:3000]}"
            )
            analysis = self.parse_json_response(response)
        except Exception as e:
            logger.warning("LLM analysis failed, using rule-based: %s", e)
            analysis = self._rule_based_check(combined)

        analysis.setdefault("status", "healthy")
        analysis.setdefault("alert", "")
        analysis.setdefault("details", "")
        analysis.setdefault("action_required", "")

        return analysis

    def _rule_based_check(self, log_content: str) -> dict:
        """基于规则的简单检查"""
        lower = log_content.lower()
        error_keywords = ["error", "exception", "traceback", "failed", "critical"]
        found = [kw for kw in error_keywords if kw in lower]

        if found:
            return {
                "status": "critical",
                "alert": f"Found error keywords in logs: {', '.join(found)}",
                "details": "Rule-based detection found potential issues",
                "action_required": "Review and fix the errors",
            }

        return {
            "status": "healthy",
            "alert": "",
            "details": "No errors detected in logs",
            "action_required": "",
        }


def log_monitor_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node function"""
    workspace_root = state["workspace_root"]

    workspace = WorkspaceManager(workspace_root)
    monitor = LogMonitor(workspace)
    result = monitor.check_logs()

    alert = result.get("alert", "")
    iteration = state.get("iteration", 0) + 1

    logger.info(
        "[log_monitor] Status: %s, Alert: %s, Iter: %d",
        result["status"],
        alert[:100] if alert else "none",
        iteration,
    )

    return {
        "alert": alert,
        "iteration": iteration,
        "current_phase": "analyze" if alert else "done",
        "messages": [
            {
                "agent": "log_monitor",
                "type": "monitor_result",
                "data": result,
            }
        ],
    }
