"""全局配置 / Global Settings"""

from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM ---
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

# --- Workspace ---
WORKSPACE_ROOT: str = os.getenv("WORKSPACE_ROOT", "./my_workspace")

# --- Workflow ---
MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "5"))

# --- Logging ---
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
