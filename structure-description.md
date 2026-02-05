## Project Structure & Responsibilities

本仓库采用 **src 布局**：所有可运行代码都位于 `src/a2a_mcp_demo/` 下；根目录只放配置、脚本与文档。整体分为三层：  
- **Capability Layer（能力层）**：`tool_server/`（MCP 工具服务）  
- **Decision Layer（决策层）**：`agent_server/`（A2A Agent 服务）  
- **Client Layer（入口层）**：`client/`（演示/调用入口）

---

### Top-level (复现与规范)

- `pyproject.toml`：项目元信息与工具配置中心（ruff/black/mypy/pytest 等），后续可配置 console scripts（例如 `autocity-agent`）。
- `README.md`：项目介绍、架构、启动方式、示例与常见问题。
- `.env.example`：环境变量模板（不含真实 key）。
- `environment.yml`：Conda 环境定义（Python 3.12 + pip）。
- `requirements.txt`：运行依赖（FastAPI/uvicorn/a2a-sdk/openai/httpx/pydantic 等）。
- `requirements-dev.txt`：开发依赖（pytest/ruff/black/mypy 等）。

---

### scripts (一键启动与冒烟测试)

- `scripts/run_local.sh`：本地一键启动（先起工具服务 7001，再起 Agent 服务 7002）。
- `scripts/smoke_test.sh`：冒烟测试（检查 Agent Card + 跑一条最小请求/CLI）。

---

### src/a2a_mcp_demo (主代码包：唯一真实代码来源)

- `src/a2a_mcp_demo/__init__.py`：包标识（可放版本号/常量；不要放业务逻辑）。

---

## Capability Layer — `tool_server/` (MCP Tool Server)

> 目标：提供“外部能力”（天气、时间、POI、地理查询等），做到 **输入输出结构化、无业务决策**，便于组合与复用。

- `tool_server/server.py`：工具服务入口（FastAPI app + `/tools/{tool}` 路由注册与启动配置）。
- `tool_server/settings.py`：工具服务配置读取（API keys、外部 API base URL、超时等）。
- `tool_server/logging.py`：工具服务结构化日志（JSONL / trace_id / latency / error_code）。
- `tool_server/schemas.py`：工具契约（单一真相源）：
  - Input/Output Pydantic 模型
  - 统一错误 `ToolError`
  - 统一响应 `ToolResponse{ok,data,error,meta}`

**Adapters（反腐层 / 适配外部 API）**
- `tool_server/adapters/amap.py`：高德 API 封装（请求、重试、字段清洗、错误映射）。
- `tool_server/adapters/openweather.py`：OpenWeather API 封装（同上）。

**Tools（薄工具 / 只做能力供给）**
- `tool_server/tools/time.py`：当前时间（纯函数，建议优先实现用于验证链路）。
- `tool_server/tools/weather.py`：天气查询（city → adapter → 结构化天气 data）。
- `tool_server/tools/poi.py`：POI 查询（city/keywords/types → adapter → 结构化 POI 列表）。

---

## Decision Layer — `agent_server/` (A2A Agent Server)

> 目标：面向用户的智能体入口。负责 **理解需求 → 选择工具 → 调用工具 → 汇总生成答案**。

- `agent_server/app.py`：FastAPI 入口（挂载 A2A 协议路由：Agent Card / task endpoints / SSE 等）。
- `agent_server/executor.py`：A2A 执行器（协议适配层）：把 A2A 任务请求转换为内部执行流程；不要在这里堆业务逻辑。
- `agent_server/agent.py`：智能体核心（单智能体 tool-use loop）：
  - 构建 messages
  - 调 OpenAI（tools/function calling）
  - 解析 tool_calls
  - 调 `tool_broker`
  - 回灌工具结果并产出最终回答
- `agent_server/tool_broker.py`：工具调用统一入口（强烈建议 async + httpx）：
  - 统一超时/重试/错误归一
  - 记录每次工具调用耗时与 trace
- `agent_server/prompts.py`：提示词模板库（建议拆成 Planner / Responder 两类）。
- `agent_server/state.py`：任务内状态（轻量）：保存本次请求中间结构化信息（city、候选 POI、已调用工具等），后续可替换成持久化存储。
- `agent_server/settings.py`：Agent 配置（OpenAI key、模型名、MCP base url、max_tool_calls、日志目录等）。
- `agent_server/logging.py`：Agent 服务结构化日志与 trace（含 LLM 调用、tool_calls、usage 等）。

---

## Client Layer — `client/` (演示入口)

- `client/cli.py`：命令行客户端（发送 query → 打印回答；`--verbose` 可打印 tool_calls/trace_id）。

---

## tests (最小测试集)

- `tests/test_tools_unit.py`：工具层单测（schema 校验、time 工具；adapter 建议用 mock/fixture）。
- `tests/test_contract.py`：契约测试（工具名称/参数/schema 对齐，防止 Agent 与 Tool Server 漂移）。
- `tests/test_smoke_cli.py`：端到端冒烟测试（起服务后跑一次 CLI/最小请求）。

---

## Data Flow (End-to-End)

1. **Client → Agent**：用户 query 发送到 `agent_server`（A2A 入口）。
2. **Agent → LLM**：`agent.py` 调用 OpenAI，模型决定是否返回 `tool_calls`（function calling）。
3. **Agent → ToolBroker → Tool Server**：`tool_broker.py` 通过 HTTP 调用 `tool_server` 的 `/tools/{tool}` 获取结构化结果。
4. **Agent 回灌工具结果**：将工具输出作为“观察（observation）”回灌给模型，必要时继续调用更多工具（有预算/去重/重试策略）。
5. **Final Answer → Client**：模型生成最终回答，`agent_server` 返回给客户端；同时写入日志与 trace（可回放）。

---

## Dependency Rules (避免屎山的导入约束)

- `agent_server` **可以依赖** `tool_server/schemas.py`（读取工具契约）
- `tool_server` **绝不依赖** `agent_server`
- `tools/` **只依赖** `adapters/` 与 `schemas.py`
- `adapters/` **不依赖** `tools/`
- `client/` **只通过 HTTP 调用 agent**（不要 import agent 内部模块）
