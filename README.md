# Night Garden / 夜花园

> 多智能体量化代码开发系统 | Multi-Agent Quant Code Development System

5 个 AI Agent 组成代码开发流水线，面向量化交易垂直赛道（自动交易 + 监控 + 资产管理），自动完成需求分析、代码编写、测试、部署和线上监控的完整闭环。

5 AI Agents form a code development pipeline for the quantitative trading vertical (auto-trading + monitoring + asset management), automating the full cycle of requirement analysis, code generation, testing, deployment, and production monitoring.

---

## 架构 / Architecture

```
用户需求 / log_monitor 告警
        ↓
  requirement_analyst   需求分析师 (LLM)
        ↓
  code_developer        代码工程师 (LLM → 写入 workspace)
        ↓
  test_engineer         测试工程师 (subprocess 真实执行)
        │
   pass ↓         fail → 回到 code_developer 重试
        ↓
  deploy_operator       运维部署 (复制到 production/)
        ↓
  log_monitor           日志监控 (LLM 分析日志)
        │
   正常 → END      异常 → 回到 requirement_analyst 闭环
```

---

## 五大 Agent / 5 Core Agents

| Agent | 中文名 | 驱动方式 | 职责 |
|-------|--------|---------|------|
| `requirement_analyst` | 需求分析师 | LLM | 接收用户需求或线上告警，拆解为开发任务（JSON） |
| `code_developer` | 代码工程师 | LLM | 生成 Python 代码 + 测试代码，真实写入 Workspace |
| `test_engineer` | 测试工程师 | LLM + subprocess | 用 subprocess 真实执行代码和 pytest，分析测试结果 |
| `deploy_operator` | 运维部署 | 代码逻辑 | 将通过测试的代码部署到 production/，写部署日志 |
| `log_monitor` | 日志监控 | LLM | 分析 production/logs/，发现异常反馈给 requirement_analyst |

| Agent | English Name | Mode | Responsibility |
|-------|-------------|------|----------------|
| `requirement_analyst` | Requirement Analyst | LLM | Parse user requirements or alerts into structured dev tasks (JSON) |
| `code_developer` | Code Developer | LLM | Generate Python code + tests, write to Workspace |
| `test_engineer` | Test Engineer | LLM + subprocess | Execute code & pytest via subprocess, analyze results |
| `deploy_operator` | Deploy Operator | Code logic | Copy approved code to production/, write deploy logs |
| `log_monitor` | Log Monitor | LLM | Analyze production/logs/, feedback alerts to requirement_analyst |

---

## Workspace 机制 / Workspace System

所有 Agent 产出物都在用户指定的 **Workspace** 目录内，通过 `workspace.yaml` 配置管理。

All agent outputs go into the user-specified **Workspace** directory, managed via `workspace.yaml`.

```yaml
# workspace.yaml
workspace_name: "my_quant_project"
code_output_dir: "./src"          # code_developer 写代码的位置
test_output_dir: "./tests"        # test_engineer 测试输出
deploy_dir: "./production"        # deploy_operator 部署目标
log_dir: "./production/logs"      # log_monitor 监控的日志
```

首次运行时自动创建默认配置和目录结构。

Auto-creates default config and directory structure on first run.

---

## 项目结构 / Project Structure

```
night_graden/                       # Agent 系统代码
├── agents/
│   ├── base.py                     # BaseAgent (LLM 封装)
│   ├── requirement_analyst.py      # 需求分析师
│   ├── code_developer.py           # 代码工程师
│   ├── test_engineer.py            # 测试工程师
│   ├── deploy_operator.py          # 运维部署
│   └── log_monitor.py              # 日志监控
├── graph/
│   ├── state.py                    # WorkflowState
│   └── workflow.py                 # StateGraph 编排
├── config/
│   ├── settings.py                 # 环境变量配置
│   └── prompts.py                  # 5 个 Agent 系统提示词
├── utils/
│   ├── logger.py                   # 统一日志
│   └── workspace.py                # Workspace 配置管理
├── main.py                         # CLI 入口
├── requirements.txt
├── .env.example
└── README.md

{WORKSPACE_ROOT}/                   # 用户 Workspace（可自定义路径）
├── workspace.yaml                  # 配置文件
├── src/                            # 生成的代码
├── tests/                          # 测试文件
└── production/                     # 部署目标
    └── logs/                       # 部署 & 运行日志
```

---

## 快速开始 / Quick Start

### 1. 安装依赖 / Install

```bash
pip install -r requirements.txt
```

### 2. 配置 / Configure

```bash
cp .env.example .env
# 编辑 .env，填入 LLM API Key 和 Workspace 路径
# Edit .env with your LLM API key and workspace path
```

### 3. 运行 / Run

```bash
python main.py
```

输入需求示例 / Example requirements:
- "实现一个 BTC/USDT 均线交叉策略"
- "编写行情数据采集模块，支持 Binance WebSocket"
- "实现回撤止损风控模块"
- "搭建历史数据回测框架"

---

## 工作流详解 / Workflow Details

1. **requirement_analyst** — 用 LLM 将需求拆解为结构化任务（task_type、description、file_name、acceptance_criteria）
2. **code_developer** — 用 LLM 生成完整 Python 代码 + pytest 测试，写入 `{workspace}/src/` 和 `{workspace}/tests/`
3. **test_engineer** — 用 `subprocess` 真实执行代码和测试，LLM 分析结果判断 pass/fail
4. **deploy_operator** — 纯代码逻辑，`shutil.copy` 到 `{workspace}/production/`，写部署日志
5. **log_monitor** — 读取最新部署日志，LLM 分析是否有异常，异常则闭环回到步骤 1

测试失败自动重试（回到 code_developer），超过 MAX_ITERATIONS 次强制终止。

Test failures auto-retry (back to code_developer), forced termination after MAX_ITERATIONS.

---

## 技术栈 / Tech Stack

- **Agent Framework**: LangGraph
- **LLM**: OpenAI GPT-4o / Anthropic Claude (可切换)
- **Code Execution**: subprocess (真实执行)
- **Testing**: pytest
- **Workspace Config**: YAML

---

## License

MIT
