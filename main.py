"""Night Garden (夜花园) — 多智能体量化代码开发系统入口 / Entry Point

5 个 Agent 组成代码开发流水线：
  requirement_analyst → code_developer → test_engineer → deploy_operator → log_monitor

启动方式：
  CLI:  python main.py
  Web:  python main.py --web
"""

from __future__ import annotations

import argparse

from config.settings import WORKSPACE_ROOT, MAX_ITERATIONS, WEB_HOST, WEB_PORT
from graph.workflow import build_graph
from utils.workspace import WorkspaceManager
from utils.logger import get_logger

logger = get_logger("main")


def run_cli():
    """CLI 模式：终端交互"""
    print("=" * 60)
    print("  Night Garden (夜花园)")
    print("  Multi-Agent Quant Code Development System")
    print("=" * 60)

    workspace = WorkspaceManager(WORKSPACE_ROOT)
    print(f"\n  Workspace:      {workspace.root}")
    print(f"  Code output:    {workspace.get_code_dir()}")
    print(f"  Test output:    {workspace.get_test_dir()}")
    print(f"  Deploy target:  {workspace.get_deploy_dir()}")
    print(f"  Log dir:        {workspace.get_log_dir()}")
    print(f"  Max iterations: {MAX_ITERATIONS}")
    print("=" * 60)

    print("\n请输入你的量化开发需求 / Enter your quant development requirement:")
    print("(示例: 实现一个 BTC/USDT 均线交叉策略)")
    user_input = input("\n> ").strip()

    if not user_input:
        print("未输入需求，退出。")
        return

    graph = build_graph()

    initial_state = {
        "messages": [],
        "workspace_root": str(workspace.root),
        "current_phase": "analyze",
        "task_description": user_input,
        "code_artifact": "",
        "code_file_path": "",
        "test_file_path": "",
        "test_result": "",
        "test_output": "",
        "deploy_status": "",
        "alert": "",
        "iteration": 0,
    }

    logger.info("Starting development workflow...")
    print("\n" + "-" * 60)
    final_state = graph.invoke(initial_state)

    print("\n" + "=" * 60)
    print("  Development Session Complete")
    print("=" * 60)

    print(f"\n  Code file:    {final_state.get('code_file_path', 'N/A')}")
    print(f"  Test result:  {final_state.get('test_result', 'N/A')}")
    print(f"  Deploy:       {final_state.get('deploy_status', 'N/A')}")
    print(f"  Iterations:   {final_state.get('iteration', 0)}")

    alert = final_state.get("alert", "")
    if alert:
        print(f"  Alert:        {alert}")

    messages = final_state.get("messages", [])
    print(f"\n  Audit Log ({len(messages)} entries):")
    for msg in messages:
        agent = msg.get("agent", "?")
        msg_type = msg.get("type", "?")
        print(f"    [{agent}] {msg_type}")

    print("\n" + "=" * 60)


def run_web(host: str, port: int):
    """Web 模式：启动 FastAPI 服务"""
    import uvicorn
    from web.app import app

    print("=" * 60)
    print("  Night Garden (夜花园) — Web UI")
    print(f"  http://{host}:{port}")
    print("=" * 60)

    uvicorn.run(app, host=host, port=port, log_level="info")


def main():
    parser = argparse.ArgumentParser(description="Night Garden — Multi-Agent Quant Code Dev System")
    parser.add_argument("--web", action="store_true", help="Start Web UI mode")
    parser.add_argument("--host", type=str, default=WEB_HOST, help=f"Web host (default: {WEB_HOST})")
    parser.add_argument("--port", type=int, default=WEB_PORT, help=f"Web port (default: {WEB_PORT})")
    args = parser.parse_args()

    if args.web:
        run_web(args.host, args.port)
    else:
        run_cli()


if __name__ == "__main__":
    main()
