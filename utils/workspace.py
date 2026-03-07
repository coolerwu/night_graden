"""Workspace 配置加载 & 目录管理 / Workspace Config & Directory Manager"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from utils.logger import get_logger

logger = get_logger("workspace")

DEFAULT_CONFIG = {
    "workspace_name": "my_quant_project",
    "code_output_dir": "./src",
    "test_output_dir": "./tests",
    "deploy_dir": "./production",
    "log_dir": "./production/logs",
}

CONFIG_FILE = "workspace.yaml"


class WorkspaceManager:
    """管理用户 Workspace 的配置和目录结构"""

    def __init__(self, workspace_root: str):
        self.root = Path(workspace_root).resolve()
        self._config: dict = {}
        self._load_or_create()

    def _load_or_create(self):
        """加载 workspace.yaml，不存在则创建默认配置"""
        config_path = self.root / CONFIG_FILE

        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
            logger.info("Loaded workspace config from %s", config_path)
        else:
            self._config = dict(DEFAULT_CONFIG)
            self.root.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            logger.info("Created default workspace config at %s", config_path)

        # 确保所有目录存在
        for dir_path in [
            self.get_code_dir(),
            self.get_test_dir(),
            self.get_deploy_dir(),
            self.get_log_dir(),
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return self._config.get("workspace_name", "workspace")

    def get_code_dir(self) -> Path:
        return self.root / self._config.get("code_output_dir", "./src")

    def get_test_dir(self) -> Path:
        return self.root / self._config.get("test_output_dir", "./tests")

    def get_deploy_dir(self) -> Path:
        return self.root / self._config.get("deploy_dir", "./production")

    def get_log_dir(self) -> Path:
        return self.root / self._config.get("log_dir", "./production/logs")

    def get_config(self) -> dict:
        return dict(self._config)

    def __repr__(self) -> str:
        return (
            f"WorkspaceManager(root={self.root}, "
            f"code={self.get_code_dir()}, "
            f"test={self.get_test_dir()}, "
            f"deploy={self.get_deploy_dir()}, "
            f"log={self.get_log_dir()})"
        )
