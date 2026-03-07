"""测试工程师 Agent / Test Engineer Agent

职责：用 subprocess 真实执行代码和测试，判断是否通过。
LLM 辅助分析测试结果。
"""

from __future__ import annotations

import subprocess
from typing import Any

from agents.base import BaseAgent
from config.prompts import TEST_ENGINEER_PROMPT
from utils.logger import get_logger

logger = get_logger("test_engineer")


class TestEngineer(BaseAgent):
    def __init__(self):
        super().__init__(name="test_engineer", system_prompt=TEST_ENGINEER_PROMPT)

    def run_tests(self, code_file_path: str, test_file_path: str) -> dict:
        """执行代码和测试"""
        results = []

        # 1. 语法检查：尝试执行主代码
        code_result = self._run_command(["python", code_file_path], timeout=30)
        results.append(f"=== Code Execution ({code_file_path}) ===\n{code_result}")

        # 2. 运行 pytest 测试
        test_result = self._run_command(
            ["python", "-m", "pytest", test_file_path, "-v", "--tb=short"],
            timeout=60,
        )
        results.append(f"=== Pytest ({test_file_path}) ===\n{test_result}")

        combined_output = "\n\n".join(results)

        # 用 LLM 分析测试结果
        analysis = self._analyze_results(combined_output)

        return {
            "test_result": analysis.get("result", "fail"),
            "test_output": combined_output,
            "analysis": analysis,
        }

    def _run_command(self, cmd: list[str], timeout: int = 30) -> str:
        """执行命令并返回输出"""
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = ""
            if proc.stdout:
                output += f"STDOUT:\n{proc.stdout}\n"
            if proc.stderr:
                output += f"STDERR:\n{proc.stderr}\n"
            output += f"Return code: {proc.returncode}"
            return output
        except subprocess.TimeoutExpired:
            return f"TIMEOUT: Command timed out after {timeout}s"
        except FileNotFoundError:
            return f"ERROR: Command not found: {cmd[0]}"

    def _analyze_results(self, output: str) -> dict:
        """用 LLM 分析测试输出"""
        try:
            response = self.invoke_llm(
                f"请分析以下测试执行结果：\n\n{output[:3000]}"
            )
            return self.parse_json_response(response)
        except Exception as e:
            logger.warning("LLM analysis failed, using rule-based: %s", e)
            return self._rule_based_analysis(output)

    def _rule_based_analysis(self, output: str) -> dict:
        """基于规则的简单分析"""
        output_lower = output.lower()
        has_error = any(
            kw in output_lower
            for kw in ["error", "exception", "traceback", "failed", "timeout"]
        )
        return {
            "result": "fail" if has_error else "pass",
            "summary": "Tests failed with errors" if has_error else "All tests passed",
            "issues": ["See output for details"] if has_error else [],
            "suggestions": [],
        }


def test_engineer_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node function"""
    code_file_path = state.get("code_file_path", "")
    test_file_path = state.get("test_file_path", "")

    engineer = TestEngineer()
    result = engineer.run_tests(code_file_path, test_file_path)

    test_passed = result["test_result"] == "pass"
    logger.info(
        "[test_engineer] Result: %s",
        "PASS" if test_passed else "FAIL",
    )

    return {
        "test_result": result["test_result"],
        "test_output": result["test_output"],
        "current_phase": "deploy" if test_passed else "develop",
        "messages": [
            {
                "agent": "test_engineer",
                "type": "test_result",
                "data": {
                    "result": result["test_result"],
                    "analysis": result["analysis"],
                },
            }
        ],
    }
