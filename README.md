# AutoCity Agent Demo (Single Agent + MCP)

一个可复现、可扩展、可调试的 **单智能体 + MCP 工具服务** Demo。

核心目标：
- 让 Agent 只负责“决策与编排”，工具服务只负责“结构化能力输出”。
- 让工程结构清晰、可替换、可扩展（后续加多智能体或 RAG 不推倒重来）。

---

## Features

- 单智能体 tool-use loop（OpenAI tool calling）
- MCP 风格工具服务（结构化输入输出）
- 统一配置与日志（trace_id 贯穿全链路）
- 可运行的 mock 模式（无 OpenAI key 也能跑通）
- 最小测试集（单测、契约、冒烟）
- 全链路 trace 文件（每次请求一份可回放记录）

---

## Architecture

```
User / Client
   |
   v
A2A Agent Server (7002)
   |  (OpenAI tool calling)
   +-----> OpenAI Model
   |
   |  (HTTP POST /tools/{name})
   v
MCP Tool Server (7001)
   |
   +-----> External APIs (OpenWeather / AMap)
```

关键原则：
- 工具服务只产出结构化 `data`，不输出自然语言。
- 自然语言只在 Agent 最后一跳生成。

---

## Project Structure

```
A2A_MCP/
├─ pyproject.toml
├─ README.md
├─ .env.example
├─ environment.yml
├─ requirements.txt
├─ requirements-dev.txt
├─ scripts/
│  ├─ run_local.sh
│  └─ smoke_test.sh
├─ src/
│  ├─ tool_server/
│  ├─ agent_server/
│  └─ client/
├─ traces/
└─ tests/
```

### Layer Responsibilities

- `tool_server/`（能力层）
  - 输入校验 → adapter → 结构化输出
  - 不做“选择调用哪个工具”的决策

- `agent_server/`（决策层）
  - LLM 规划工具调用
  - ToolBroker 统一调用工具
  - 汇总工具结果并生成最终回答

- `client/`（入口层）
  - CLI 发送请求与展示结果

- `traces/`（回放层）
  - 每个请求输出一个结构化 JSON，用于复现与排障

---

## Quickstart

### 1) Create & activate env

```bash
conda create -n A2A_MCP python=3.12 -y
conda activate A2A_MCP
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2) Configure environment variables

Create `.env` from the example in project root:

```bash
cp .env.example .env
```

然后按需修改其中的配置。常见最小配置：

```bash
OPENAI_API_KEY=your_openai_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
AMAP_API_KEY=your_amap_api_key
```

如果你要切到兼容 OpenAI API 的第三方网关，也可以在 `.env` 里设置：

```bash
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
```

常见示例：

```bash
# ChatAnywhere（中国国内）
OPENAI_BASE_URL=https://api.chatanywhere.tech/v1

# ChatAnywhere（中国境外）
OPENAI_BASE_URL=https://api.chatanywhere.org/v1
```

如果切回 OpenAI 官方 API，建议直接注释掉或删除 `OPENAI_BASE_URL`，不要保留第三方地址。

### 3) Start services

```bash
bash scripts/run_local.sh
```

### 4) Call the agent

注意：CLI 命令需要能找到 `src/` 下的包。你可以：
- 在命令前加 `PYTHONPATH=src`
- 或者先执行 `export PYTHONPATH=src`（只对当前终端生效）

```bash
PYTHONPATH=src python -m client.cli "北京今天天气怎么样？" --verbose
```

如果遇到超时（复杂问题可能需要更久），可增加超时：

```bash
PYTHONPATH=src python -m client.cli "我周末去上海，帮我看看天气，根据这个以及逛景点，两天行程怎么安排？" --timeout 120 --verbose
```

也可以直接用 HTTP：

```bash
curl -i -H "Content-Type: application/json" \
  -d '{"query":"北京现在气温多少度？"}' \
  http://localhost:7002/v1/ask
```

---

## Mock Mode

无 OpenAI key 时可使用 mock 模式：

```bash
export A2A_MCP_MOCK_LLM=true
export A2A_MCP_MCP_BASE_URL=inproc
```

说明：
- 环境变量优先级高于 `.env` 文件
- 如果之前 `export` 过 mock 变量，后续需要显式关闭：
  - `unset A2A_MCP_MOCK_LLM` 或 `export A2A_MCP_MOCK_LLM=false`
  - `unset A2A_MCP_MCP_BASE_URL` 或改回真实地址

---

## Traces (Request Replay)

每次请求会输出一个结构化 trace 文件：`traces/<timestamp>_<trace_id>.json`。  
内容包含：
- 关键时间戳与耗时
- 工具调用序列（输入/输出/错误）
- LLM 调用摘要（模型、temperature、tool_calls）
- 最终回答

你可以将 trace 文件用于：
- 离线复现与回放
- 排查“LLM 规划/工具参数/工具返回/渲染”的问题
- 回归测试（同一批 query 比较输出差异）

---

## Tools

- `time`：当前时间
- `weather`：天气（OpenWeather）
- `poi`：附近 POI（AMap）

---

## Tests

```bash
PYTHONPATH=src pytest -q
```

建议的测试方式：
- 仅跑工具层单测：
  - `PYTHONPATH=src pytest -q tests/test_tools_unit.py`
- 验证契约（工具/agent schema 对齐）：
  - `PYTHONPATH=src pytest -q tests/test_contract.py`
- 冒烟测试（mock 模式，不依赖外部 API）：
  - `PYTHONPATH=src pytest -q tests/test_smoke_cli.py`

---

## Configuration

常用环境变量（详见 `.env.example`）：
- `OPENAI_API_KEY`：OpenAI API Key（必需，除非使用 mock）
- `OPENAI_BASE_URL`：OpenAI-compatible API Base URL。使用 OpenAI 官方 API 时建议留空或注释掉；使用第三方兼容网关时再显式设置
- `OPENWEATHER_API_KEY`：OpenWeather Key（天气工具必需）
- `AMAP_API_KEY`：高德 Key（POI/地理相关工具必需）
- `A2A_MCP_OPENAI_MODEL`：OpenAI 模型名（默认 `gpt-4o-mini`）
- `A2A_MCP_OPENAI_TEMPERATURE`：LLM temperature（默认 `0.2`）
- `A2A_MCP_OPENAI_TIMEOUT_S`：OpenAI 超时秒数（默认 20）
- `A2A_MCP_MAX_TOOL_CALLS`：单次请求最多允许的工具调用次数（默认 `3`）
- `A2A_MCP_TOOL_ARG_RETRY_LIMIT`：工具参数校验失败后，允许模型自动重试生成参数的次数（默认 `1`）
- `A2A_MCP_AGENT_HOST` / `A2A_MCP_AGENT_PORT`：Agent 服务监听地址（默认 `0.0.0.0:7002`）
- `A2A_MCP_TOOL_HOST` / `A2A_MCP_TOOL_PORT`：Tool 服务监听地址（默认 `0.0.0.0:7001`）
- `A2A_MCP_AGENT_BASE_URL`：CLI 与冒烟脚本默认访问的 Agent 地址（默认 `http://localhost:7002`）
- `A2A_MCP_MCP_BASE_URL`：工具服务地址（默认 `http://localhost:7001`）
- `A2A_MCP_AGENT_REQUEST_TIMEOUT_S`：Agent 调工具服务的 HTTP 超时（默认 `10`）
- `A2A_MCP_TOOL_REQUEST_TIMEOUT_S`：Tool 服务调外部 API 的超时（默认 `8`）
- `A2A_MCP_MOCK_LLM`：是否启用 mock（`true/false`）
- `A2A_MCP_TRACE_ENABLED`：是否写入 trace 文件（`true/false`）
- `A2A_MCP_TRACE_DIR`：trace 输出目录（默认 `traces`）
- `A2A_MCP_RELOAD`：本地启动时是否启用 uvicorn reload（默认 `false`）

模型说明：
- 默认模型为 `gpt-4o-mini`（代码内默认值）
- 如需切换，设置 `.env`：
  `A2A_MCP_OPENAI_MODEL=gpt-4o`

兼容网关说明（实测经验）：
- 使用第三方兼容 OpenAI 的网关时，即使你配置的是 `gpt-4o-mini`，实际路由到的后端模型版本也可能不同。
- 本项目排查中，第三方免费线路曾出现“名义上是 `gpt-4o-mini`，实际表现更接近 `gpt-4o-mini-ca`”的情况，tool calling 参数稳定性会变差，可能出现遗漏 `city` 之类的参数问题。
- 切换到 OpenAI 官方 API，或切换到第三方付费线路后，请求恢复为正常 `gpt-4o-mini`，tool calling 表现更稳定。
- 这类问题通常不是本项目把参数吃掉了，而是上游模型/兼容层实际能力与名义模型不一致。

---

## Troubleshooting

- 端口占用：优先调整 `A2A_MCP_AGENT_PORT`、`A2A_MCP_TOOL_PORT`，如果 tool 端口变了，同时更新 `A2A_MCP_MCP_BASE_URL`
- 外部 API 报错：确认 key 配置是否正确
- 切换 OpenAI 官方 API 后仍然异常：检查 `.env` 里是否残留了 `OPENAI_BASE_URL`。如已切回官方，建议将其删除或注释掉
- 第三方兼容网关 tool calling 不稳定：先确认实际路由的模型版本，再区分是项目问题还是上游模型/线路问题

---

## Roadmap

- AMap 城市 geocode（替换 POI 默认坐标）
- SSE streaming（端到端流式输出）
- 多智能体与 RAG 扩展
