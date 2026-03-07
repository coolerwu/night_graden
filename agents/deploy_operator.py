"""运维部署 Agent / Deploy Operator Agent

职责：将通过测试的代码部署到 production 目录，写部署日志。
纯代码逻辑，不使用 LLM。
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.logger import get_logger
from utils.workspace import WorkspaceManager

logger = get_logger("deploy_operator")


class DeployOperator:
    def __init__(self, workspace: WorkspaceManager):
        self.workspace = workspace

    def deploy(self, code_file_path: str, test_file_path: str = "") -> dict:
        """将代码从 workspace/src 部署到 workspace/production"""
        src = Path(code_file_path)
        if not src.exists():
            return {"status": "failed", "error": f"Source file not found: {src}"}

        deploy_dir = self.workspace.get_deploy_dir()
        dest = deploy_dir / src.name

        try:
            shutil.copy2(src, dest)
            logger.info("[deploy_operator] Deployed: %s → %s", src, dest)

            # 写部署日志
            log_entry = self._write_deploy_log(src.name, dest)

            return {
                "status": "success",
                "source": str(src),
                "destination": str(dest),
                "log": log_entry,
            }
        except Exception as e:
            logger.error("[deploy_operator] Deploy failed: %s", e)
            return {"status": "failed", "error": str(e)}

    def _write_deploy_log(self, file_name: str, dest: Path) -> str:
        """写部署日志"""
        log_dir = self.workspace.get_log_dir()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"deploy_{timestamp}.log"

        log_entry = (
            f"[{datetime.utcnow().isoformat()}] DEPLOY\n"
            f"  File: {file_name}\n"
            f"  Destination: {dest}\n"
            f"  Status: SUCCESS\n"
        )

        log_file.write_text(log_entry, encoding="utf-8")
        logger.info("[deploy_operator] Deploy log: %s", log_file)
        return log_entry


def deploy_operator_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node function"""
    workspace_root = state["workspace_root"]
    code_file_path = state.get("code_file_path", "")

    workspace = WorkspaceManager(workspace_root)
    operator = DeployOperator(workspace)
    result = operator.deploy(code_file_path)

    success = result["status"] == "success"
    logger.info(
        "[deploy_operator] %s",
        "Deploy successful" if success else f"Deploy failed: {result.get('error', '')}",
    )

    return {
        "deploy_status": result["status"],
        "current_phase": "monitor",
        "messages": [
            {
                "agent": "deploy_operator",
                "type": "deploy_result",
                "data": result,
            }
        ],
    }
