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

# --- Exchange ---
EXCHANGE_MODE: str = os.getenv("EXCHANGE_MODE", "mock")  # mock | live
EXCHANGE_NAME: str = os.getenv("EXCHANGE_NAME", "binance")
EXCHANGE_API_KEY: str = os.getenv("EXCHANGE_API_KEY", "")
EXCHANGE_SECRET: str = os.getenv("EXCHANGE_SECRET", "")
EXCHANGE_PASSWORD: str = os.getenv("EXCHANGE_PASSWORD", "")

# --- Trading ---
TRADING_SYMBOL: str = os.getenv("TRADING_SYMBOL", "BTC/USDT")
TRADING_TIMEFRAME: str = os.getenv("TRADING_TIMEFRAME", "1h")
MAX_POSITION_SIZE: float = float(os.getenv("MAX_POSITION_SIZE", "1.0"))
MAX_DRAWDOWN_PCT: float = float(os.getenv("MAX_DRAWDOWN_PCT", "10.0"))
MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))

# --- Logging ---
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# --- Initial Capital ---
INITIAL_CAPITAL: float = float(os.getenv("INITIAL_CAPITAL", "10000.0"))
