"""工作流编排 / Workflow Graph Construction

开发流水线：
requirement_analyst → code_developer → test_engineer → deploy_operator → log_monitor
                 ↑         ↑                                                  │
                 │         └── test fail 时重试 ──────────────────────────────│
                 └── log_monitor 发现异常时闭环 ──────────────────────────────┘
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from agents.requirement_analyst import requirement_analyst_node
from agents.code_developer import code_developer_node
from agents.test_engineer import test_engineer_node
from agents.deploy_operator import deploy_operator_node
from agents.log_monitor import log_monitor_node
from config.settings import MAX_ITERATIONS
from graph.state import WorkflowState
from utils.logger import get_logger

logger = get_logger("workflow")


def route_after_test(state: WorkflowState) -> str:
    """测试后路由：pass → deploy，fail → 回到 code_developer 重试"""
    test_result = state.get("test_result", "fail")
    iteration = state.get("iteration", 0)

    if test_result == "pass":
        logger.info("[workflow] Tests passed, proceeding to deploy")
        return "deploy_operator"

    if iteration >= MAX_ITERATIONS:
        logger.info("[workflow] Max iterations reached, ending despite test failure")
        return END

    logger.info("[workflow] Tests failed, retrying code_developer")
    return "code_developer"


def route_after_monitor(state: WorkflowState) -> str:
    """监控后路由：有告警 → 回到 requirement_analyst，无告警 → 结束"""
    alert = state.get("alert", "")
    iteration = state.get("iteration", 0)

    if iteration >= MAX_ITERATIONS:
        logger.info("[workflow] Max iterations (%d) reached, ending", MAX_ITERATIONS)
        return END

    if alert:
        logger.info("[workflow] Alert detected, looping back to requirement_analyst")
        return "requirement_analyst"

    logger.info("[workflow] All clear, workflow complete")
    return END


def build_graph() -> StateGraph:
    """构建并编译开发工作流图"""
    graph = StateGraph(WorkflowState)

    # 添加节点
    graph.add_node("requirement_analyst", requirement_analyst_node)
    graph.add_node("code_developer", code_developer_node)
    graph.add_node("test_engineer", test_engineer_node)
    graph.add_node("deploy_operator", deploy_operator_node)
    graph.add_node("log_monitor", log_monitor_node)

    # 入口
    graph.set_entry_point("requirement_analyst")

    # 固定边
    graph.add_edge("requirement_analyst", "code_developer")
    graph.add_edge("code_developer", "test_engineer")
    graph.add_edge("deploy_operator", "log_monitor")

    # 条件边
    graph.add_conditional_edges(
        "test_engineer",
        route_after_test,
        {
            "deploy_operator": "deploy_operator",
            "code_developer": "code_developer",
            END: END,
        },
    )
    graph.add_conditional_edges(
        "log_monitor",
        route_after_monitor,
        {
            "requirement_analyst": "requirement_analyst",
            END: END,
        },
    )

    return graph.compile()
