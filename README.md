# Night Garden / 夜花园

> 多智能体量化交易系统 | Multi-Agent Quantitative Trading System

自动交易 + 实时监控 + 资产管理，五个 AI Agent 协同工作的量化交易闭环系统。

Auto-trading + Real-time Monitoring + Asset Management — a closed-loop quant trading system powered by 5 collaborative AI agents.

---

## 架构 / Architecture

```
                    ┌──────────────────┐
                    │  market_sensor   │  市场感知器 / Market Sensor
                    │  采集行情 + LLM分析│
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ strategy_engine  │  策略引擎 / Strategy Engine
                    │  信号生成(代码逻辑) │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  risk_guardian   │  风控守卫 / Risk Guardian
                    │  预检+拦截(代码逻辑)│
                    └────────┬─────────┘
                             │
                ┌────────────┤ 通过/拦截
                │            │
       ┌────────▼────────┐   │
       │ trade_executor  │   │  交易执行器 / Trade Executor
       │  下单执行        │   │
       └────────┬────────┘   │
                │            │
                └────────────┤
                             │
                    ┌────────▼─────────┐
                    │  asset_manager   │  资产管家 / Asset Manager
                    │  资产统计 + LLM报告│
                    └──────────────────┘
```

---

## 五大 Agent / 5 Core Agents

| Agent | 中文名 | 驱动方式 | 职责 |
|-------|--------|---------|------|
| **market_sensor** | 市场感知器 | LLM + 规则 | 接入行情数据源，清洗标准化数据，LLM 辅助趋势分析 |
| **strategy_engine** | 策略引擎 | 纯代码 | 加载可插拔策略模块，基于行情生成买卖信号 |
| **risk_guardian** | 风控守卫 | 纯代码 | 仓位上限、回撤检查、单笔限额，拦截高风险交易 |
| **trade_executor** | 交易执行器 | 纯代码 | 通过交易所 API 下单/撤单，管理订单生命周期 |
| **asset_manager** | 资产管家 | LLM + 规则 | 跟踪余额、持仓、盈亏，LLM 辅助生成资产报告 |

| Agent | English Name | Mode | Responsibility |
|-------|-------------|------|----------------|
| **market_sensor** | Market Sensor | LLM + Rules | Collect market data, normalize candles/tickers, LLM-assisted trend analysis |
| **strategy_engine** | Strategy Engine | Code Only | Load pluggable strategy modules, generate buy/sell signals from market data |
| **risk_guardian** | Risk Guardian | Code Only | Position limits, drawdown checks, single-order caps, block high-risk trades |
| **trade_executor** | Trade Executor | Code Only | Execute orders via exchange API, manage order lifecycle |
| **asset_manager** | Asset Manager | LLM + Rules | Track balance, positions, PnL, LLM-assisted portfolio reports |

---

## 项目结构 / Project Structure

```
night_graden/
├── agents/                     # 5 核心 Agent
│   ├── base.py                 # Agent 基类 (LLM 封装)
│   ├── market_sensor.py        # 市场感知器
│   ├── strategy_engine.py      # 策略引擎
│   ├── trade_executor.py       # 交易执行器
│   ├── risk_guardian.py        # 风控守卫
│   └── asset_manager.py        # 资产管家
├── graph/                      # LangGraph 工作流
│   ├── state.py                # TradingState 状态定义
│   └── workflow.py             # StateGraph 构建 & 路由
├── strategies/                 # 可插拔交易策略
│   ├── base_strategy.py        # 策略基类
│   ├── ma_crossover.py         # 均线交叉策略
│   └── grid_trading.py         # 网格交易策略
├── models/                     # Pydantic 数据模型
│   ├── market_data.py          # K线、Ticker、OrderBook
│   ├── signal.py               # 交易信号
│   ├── order.py                # 订单
│   └── position.py             # 持仓 & 资产组合
├── config/                     # 配置
│   ├── settings.py             # 环境变量 & 全局配置
│   └── prompts.py              # Agent LLM 提示词
├── utils/                      # 工具模块
│   ├── logger.py               # 统一日志
│   └── exchange_client.py      # 交易所客户端 (Mock + Live)
├── api/                        # FastAPI 后端 API
│   ├── server.py               # 服务入口 + WebSocket
│   └── routes/
│       ├── trading.py          # 交易接口
│       └── portfolio.py        # 资产接口
├── frontend/                   # React 前端 Dashboard
│   ├── src/
│   │   ├── components/         # UI 组件
│   │   ├── hooks/              # 自定义 Hooks
│   │   ├── services/           # API 调用
│   │   └── App.tsx             # 主页面
│   └── package.json
├── main.py                     # CLI 入口
├── requirements.txt
└── .env.example
```

---

## 快速开始 / Quick Start

### 1. 安装依赖 / Install Dependencies

```bash
# 后端 / Backend
pip install -r requirements.txt

# 前端 / Frontend
cd frontend && npm install
```

### 2. 配置环境 / Configure

```bash
cp .env.example .env
# 编辑 .env，填入 API Key / Edit .env with your API keys
```

### 3. 运行 / Run

**CLI 模式 / CLI Mode:**
```bash
python main.py
```

**Web 模式 / Web Mode:**
```bash
# 启动 API 服务 / Start API server
uvicorn api.server:app --host 0.0.0.0 --port 8000

# 启动前端 / Start frontend (另一个终端)
cd frontend && npm run dev
```

访问 / Visit: `http://localhost:3000`

---

## 交易所支持 / Exchange Support

通过 `.env` 中的 `EXCHANGE_MODE` 切换模式：

| 模式 Mode | 说明 Description |
|-----------|-----------------|
| `mock` | 模拟交易，无需 API Key，用于开发和回测 / Simulated trading for dev & backtesting |
| `live` | 实盘交易，需要交易所 API Key / Live trading via exchange API |

支持的交易所 (通过 ccxt)：Binance, OKX, Bybit 等。

Supported exchanges (via ccxt): Binance, OKX, Bybit, etc.

---

## 策略开发 / Strategy Development

继承 `BaseStrategy` 即可添加自定义策略：

Extend `BaseStrategy` to add custom strategies:

```python
from strategies.base_strategy import BaseStrategy
from models.market_data import Kline
from models.signal import TradeSignal, SignalType

class MyStrategy(BaseStrategy):
    name = "my_strategy"

    def evaluate(self, klines: list[Kline], current_position: float = 0.0) -> TradeSignal | None:
        # 你的策略逻辑 / Your strategy logic
        price = klines[-1].close
        if some_condition:
            return TradeSignal(
                symbol=klines[-1].symbol,
                signal_type=SignalType.BUY,
                price=price,
                strategy_name=self.name,
                confidence=0.8,
                reason="My custom signal",
            )
        return None
```

---

## 风控规则 / Risk Rules

| 规则 Rule | 默认值 Default | 说明 |
|-----------|---------------|------|
| 最大持仓 Max Position | 1.0 BTC | 超过则拦截买入信号 |
| 最大回撤 Max Drawdown | 10% | 触发后暂停所有买入 |
| 单笔上限 Single Order | 30% of portfolio | 单笔不超过总资产 30% |

---

## 技术栈 / Tech Stack

- **Agent Framework**: LangGraph
- **LLM**: OpenAI GPT-4o / Anthropic Claude (可切换)
- **Exchange**: ccxt (统一交易所接口)
- **Backend API**: FastAPI + WebSocket
- **Frontend**: React + TypeScript + Vite
- **Data Models**: Pydantic v2

---

## License

MIT
