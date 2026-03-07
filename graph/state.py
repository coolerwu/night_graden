"""开发工作流状态 / Development Workflow State"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class WorkflowState(TypedDict):
    """LangGraph 工作流状态定义

    5 个 Agent 组成代码开发流水线：
    requirement_analyst → code_developer → test_engineer → deploy_operator → log_monitor
    """

    # 审计日志（append-only）
    messages: Annotated[list[dict], operator.add]

    # Workspace 根路径
    workspace_root: str

    # 当前阶段
    current_phase: str  # analyze → develop → test → deploy → monitor

    # requirement_analyst 输出
    task_description: str  # JSON 格式的任务描述

    # code_developer 输出
    code_artifact: str  # 生成的代码内容
    code_file_path: str  # 代码写入的文件路径
    test_file_path: str  # 测试文件路径

    # test_engineer 输出
    test_result: str  # pass / fail
    test_output: str  # 测试执行的 stdout/stderr

    # deploy_operator 输出
    deploy_status: str  # success / failed

    # log_monitor 输出
    alert: str  # 告警信息（空=正常）

    # 循环计数
    iteration: int
