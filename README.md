# AutoCity Agent Demo (Single Agent + MCP)

一个可复现的 **单智能体 + MCP 工具服务** 小项目：用户用自然语言提问，Agent 使用大模型决定是否调用 MCP 工具（天气/时间/POI/地理能力等），再生成最终回答。

> 先把单智能体 + MCP 做扎实；后续再加多智能体 + RAG，避免一上来架构过度复杂。

---

## What’s in this repo

### Key files

- `mcp_server.py`：MCP 工具服务（默认端口 **7001**），对外提供 `/tools/<tool_name>` 的 HTTP 调用入口
- `a2a_agent_advanced.py`：A2A Agent 服务（默认端口 **7002**），负责 LLM 决策 + 工具调用编排
- `requirements.txt`：依赖列表
- `test_a2a_advanced.ipynb`：简单交互/测试示例
- `a2a和mcp_demo.pdf`：项目说明/演示材料

---

## Architecture

```
User / Client
   |
   v
A2A Agent Server (7002)
   |  (OpenAI tools / function calling)
   +-----> OpenAI Model
   |
   |  (HTTP POST /tools/<name>)
   v
MCP Tool Server (7001)
   |
   +-----> External APIs (OpenWeather / AMap)
```

### Structure
```
A2A_MCP/
├─ pyproject.toml                 # 项目元信息 + 工具配置（ruff/black/mypy/pytest 等）
├─ README.md                      # 使用说明/架构/启动方式/示例
├─ LICENSE                        # 许可证
├─ .gitignore                     # 忽略规则（.env、logs、traces、__pycache__…）
├─ .env.example                   # 环境变量模板（不含真实 key）
├─ environment.yml                # conda 环境（主入口，Python=3.12）
├─ requirements.txt               # 运行依赖（pip 备选/CI 用）
├─ requirements-dev.txt           # 开发依赖（测试/格式化/类型检查）
│
├─ scripts/                       # 本地脚本（减少记命令）
│  ├─ run_local.sh                # 一键启动：先 tool_server(7001) 再 agent_server(7002)
│  └─ smoke_test.sh               # 冒烟测试：Agent Card + 最小请求/CLI
│
├─ src/                           # src 布局：所有真实代码都放这里
│  └─ a2a_mcp_demo/               # 主 Python 包（import 都从这里开始）
│     ├─ __init__.py              # 包标识/版本（可选）
│     │
│     ├─ tool_server/             # MCP 工具服务（能力层：只提供能力，不做业务决策）
│     │  ├─ __init__.py
│     │  ├─ server.py             # FastAPI app + /tools/{tool} 路由注册/启动入口
│     │  ├─ settings.py           # 读取 env/集中配置（keys、timeout、base_url 等）
│     │  ├─ logging.py            # 工具侧结构化日志（trace_id、latency、error_code）
│     │  ├─ schemas.py            # 工具契约：Input/Output/Error/统一 ToolResponse（单一真相源）
│     │  ├─ adapters/             # 外部 API 适配器（反腐层：清洗字段/错误映射/重试）
│     │  │  ├─ __init__.py
│     │  │  ├─ amap.py            # 高德 API 封装
│     │  │  └─ openweather.py     # OpenWeather API 封装
│     │  └─ tools/                # MCP tools（薄工具：校验输入→调 adapter→返回结构化 data）
│     │     ├─ __init__.py
│     │     ├─ time.py            # 当前时间工具（建议先实现，用来验证链路）
│     │     ├─ weather.py         # 天气工具
│     │     └─ poi.py             # POI 工具
│     │
│     ├─ agent_server/            # A2A Agent 服务（决策层：理解→选工具→调用→汇总回答）
│     │  ├─ __init__.py
│     │  ├─ app.py                # FastAPI 入口：挂 A2A 协议路由（Agent Card/任务/SSE）
│     │  ├─ executor.py           # 协议适配层：把 A2A 任务请求转成内部执行（不堆业务逻辑）
│     │  ├─ agent.py              # 智能体核心：LLM + tool-use loop + 最终回答生成
│     │  ├─ tool_broker.py        # 统一调 MCP：httpx async、超时/重试/错误归一/日志
│     │  ├─ prompts.py            # Prompt 模板（Planner/Responder 分离，避免屎山）
│     │  ├─ state.py              # 任务内状态（本次请求中间信息；后续可替换持久化）
│     │  ├─ settings.py           # Agent 配置（模型名、MCP_BASE_URL、预算、日志目录等）
│     │  └─ logging.py            # Agent 侧结构化日志/trace（含 tool_calls、usage 可选）
│     │
│     └─ client/                  # 调用入口层（演示/调试）
│        ├─ __init__.py
│        └─ cli.py                # 命令行客户端（--verbose 打印 tool_calls/trace_id）
│
└─ tests/                         # 测试集（防回归、保证可维护）
   ├─ test_tools_unit.py           # 工具单测（优先纯逻辑；外部 API 用 mock/fixture）
   ├─ test_contract.py             # 契约测试（工具名称/参数/schema 对齐，防漂移）
   └─ test_smoke_cli.py            # 端到端冒烟测试（起服务后跑一次最小链路）

```

### Runtime ports

- MCP Tool Server: `http://localhost:7001`
- A2A Agent Server: `http://localhost:7002`

---

## Quickstart (Conda)

### 1) Create & activate conda env

```bash
conda create -n A2A_MCP python=3.12 -y
conda activate A2A_MCP
pip install -r requirements.txt
```

### 2) Configure environment variables

Create a `.env` in project root (do **NOT** commit it):

```bash
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# OpenWeather (required if you use weather tools)
OPENWEATHER_API_KEY=your_openweather_api_key

# AMap (required if you use AMap tools)
AMAP_API_KEY=your_amap_api_key
```

> 建议额外加一个 `.env.example`（无真实 key）给别人复制使用，并在 `.gitignore` 忽略 `.env`。

### 3) Start servers (two terminals)

**Terminal A: MCP tool server**

```bash
python mcp_server.py
```

**Terminal B: A2A agent server**

```bash
python a2a_agent_advanced.py
```

### 4) Try a quick demo

Run the provided notebook:

```bash
jupyter notebook test_a2a_advanced.ipynb
```

Or (optional) call the agent with a tiny Python snippet (requires `python-a2a`):

```python
from python_a2a import A2AClient

client = A2AClient(base_url="http://localhost:7002")
print(client.ask("北京今天天气怎么样？"))
```

---

## Available Tools (current)

### Basic tools

- `calculator`
- `get_current_time`
- `get_current_weather`

### AMap tools

- `get_city_poi`
- `amap_geocode`
- `amap_place_around`
- `amap_adcode_search`
- `amap_weather_forecast`

### Notes / TODOs

- `amap_route_planning`：当前 **Agent 侧 schema 已声明**，但若 **MCP 端未实现**会导致调用失败（建议补齐或先移除声明）
- SSE 流式输出：目前有基础函数/思路，但尚未形成端到端 streaming demo（建议后续补一个真正流式工具作为展示）

---

## Demo Queries

- 「北京今天天气怎么样？」
- 「帮我计算 3*100+20」
- 「现在几点了？」
- 「推荐东京的热门景点」
- 「我在上海外滩，附近有什么好吃的？」

---

## Troubleshooting

### Port already in use

- Free the ports or change them in code:
  - MCP: `7001`
  - Agent: `7002`

### Weather tool returns “city not found”

- OpenWeather 的城市名更偏向英文/标准拼写；AMap 更适合中文地名
- 建议：在 Agent 侧做一次“城市名规范化”（后续重构项）

### AMap returns empty results

- 检查 `AMAP_API_KEY`
- 部分关键词/类型需要调整（例如“火锅”“景点”“商场”等）

---

## Recommended next steps (to make this demo “production-like”)

如果你准备把这个 demo 变成“工程化可维护的样例”，建议按顺序做：

1. **单一真相源（schema）**：把工具的 input/output/error schema 从 Agent 手写迁移到 MCP 端统一导出
2. **ToolBroker**：抽一个统一工具调用层（超时/重试/限流/结构化错误/结构化日志）
3. **结构化输出**：工具返回 JSON `data`，最终由 Agent 渲染为自然语言（便于多工具组合）
4. **Trace 回放**：每次请求生成 `trace_id`，保存 tool_calls 与结果，便于复现/调试
5. **Tests**：至少包含工具单测 + 契约测试（防止 Agent/MCP schema 漂移）

---

## Roadmap (later)

- Multi-agent (Supervisor + Specialists)
- RAG as a capability service (retrieve/rerank/cite as tools)
- Streaming UI (SSE) demo

---

## License

Choose one (e.g., MIT / Apache-2.0). For demos, MIT is common.