"""Agent 基类 / Base Agent with LLM support"""

from __future__ import annotations

import json
from config.settings import LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, ANTHROPIC_API_KEY
from utils.logger import get_logger

logger = get_logger("base_agent")


class BaseAgent:
    """支持 OpenAI / Anthropic 双后端的 Agent 基类"""

    def __init__(self, name: str, system_prompt: str = ""):
        self.name = name
        self.system_prompt = system_prompt
        self._llm = self._build_llm()

    def _build_llm(self):
        if LLM_PROVIDER == "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=LLM_MODEL or "claude-sonnet-4-20250514",
                anthropic_api_key=ANTHROPIC_API_KEY,
                max_tokens=2048,
            )
        else:
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=LLM_MODEL or "gpt-4o",
                api_key=OPENAI_API_KEY,
                temperature=0.3,
            )

    def invoke_llm(self, user_message: str) -> str:
        from langchain_core.messages import SystemMessage, HumanMessage

        messages = []
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))
        messages.append(HumanMessage(content=user_message))

        response = self._llm.invoke(messages)
        return response.content

    def parse_json_response(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("[%s] Failed to parse LLM JSON response", self.name)
            return {"raw": text}
