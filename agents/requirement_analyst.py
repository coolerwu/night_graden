"""需求分析师 Agent / Requirement Analyst Agent

职责：接收用户需求或 log_monitor 告警，拆解为开发任务。
LLM 驱动。
"""

from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from config.prompts import REQUIREMENT_ANALYST_PROMPT
from utils.logger import get_logger

logger = get_logger("requirement_analyst")


class RequirementAnalyst(BaseAgent):
    def __init__(self):
        super().__init__(name="requirement_analyst", system_prompt=REQUIREMENT_ANALYST_PROMPT)

    def analyze(self, user_input: str, alert: str = "") -> dict:
        """分析需求或告警，输出任务描述"""
        if alert:
            prompt = (
                f"线上监控发现以下告警，请分析并拆解为修复任务：\n"
                f"告警内容：{alert}\n"
                f"原始需求上下文：{user_input}"
            )
        else:
            prompt = f"用户需求：{user_input}"

        response = self.invoke_llm(prompt)
        task = self.parse_json_response(response)

        # 确保必要字段存在
        task.setdefault("task_type", "other")
        task.setdefault("description", user_input)
        task.setdefault("file_name", "task.py")
        task.setdefault("acceptance_criteria", [])

        return task


def requirement_analyst_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node function"""
    user_input = state.get("task_description", "")
    alert = state.get("alert", "")

    analyst = RequirementAnalyst()

    if alert:
        logger.info("[requirement_analyst] Analyzing alert: %s", alert[:100])
    else:
        logger.info("[requirement_analyst] Analyzing requirement: %s", user_input[:100])

    task = analyst.analyze(user_input, alert)

    import json
    task_json = json.dumps(task, ensure_ascii=False)
    logger.info("[requirement_analyst] Task: %s", task_json[:200])

    return {
        "task_description": task_json,
        "alert": "",  # 清除告警
        "current_phase": "develop",
        "messages": [
            {
                "agent": "requirement_analyst",
                "type": "task_analysis",
                "data": task,
            }
        ],
    }
