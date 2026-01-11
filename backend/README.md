# Terra AIOps Platform Backend

Terra AIOps Platform 是一个智能网络运维平台后端服务，提供 SDN 控制器管理、网络拓扑可视化、知识图谱、MCP (Model Context Protocol) 集成和智能运维分析等功能。

## 技术栈

- **框架**: FastAPI
- **Python 版本**: >= 3.12
- **数据库**: 
  - PostgreSQL (关系型数据存储)
  - Neo4j (图数据库，用于知识图谱)
- **AI/LLM**: 
  - LangChain (LLM 编排)
  - LangGraph (工作流引擎)
  - OpenAI API (可配置)
- **数据库迁移**: Alembic
- **缓存**: 支持内存缓存和 Redis

## 核心功能

### 1. SDN 控制器管理
- 支持多种 SDN 控制器类型（OpenDaylight、ONOS、Terra 等）
- 控制器连接测试和状态监控
- 网络拓扑同步和快照管理
- 监控数据和日志收集

### 2. 知识图谱
- 基于 Neo4j 的网络知识图谱存储
- 网络拓扑关系建模
- 图谱数据查询和可视化支持
- Mermaid 图表转换

### 3. MCP 服务器管理
- Model Context Protocol 服务器配置
- 工具列表查询和动态调用
- 多 MCP 服务器支持

### 4. 智能运维
- 根因分析 (RCA) 引擎
- 规则引擎（关键词匹配、正则匹配、FSM 处理）
- 告警收集和处理
- AI Agent 工作流（基于 ReAct 模式）

## 项目结构

```
backend/
├── apps/
│   ├── cache/              # 缓存管理（内存/Redis）
│   ├── graph_db/           # Neo4j 图数据库操作
│   ├── llm/                # LLM 助手封装
│   ├── models/             # 数据模型
│   │   ├── service/        # 服务层模型（API、数据库）
│   │   └── workflow/       # 工作流模型
│   ├── rca/                # 根因分析模块
│   │   ├── collector/      # 数据收集器
│   │   └── rule_engine/    # 规则引擎
│   ├── router/             # API 路由
│   ├── service/            # 业务服务层
│   ├── utils/              # 工具类
│   ├── workflow/           # AI 工作流引擎
│   │   ├── agent/          # AI Agent 实现
│   │   ├── client/         # MCP 客户端
│   │   └── node/           # 工作流节点
│   └── api.py              # API 聚合路由
├── alembic/                # 数据库迁移脚本
├── etc/
│   └── config.yaml         # 应用配置文件
├── test/                   # 测试用例
├── .env.example            # 环境变量示例
├── main.py                 # 应用入口
├── pyproject.toml          # 项目依赖配置
└── alembic.ini             # Alembic 配置
```

## 快速开始

### 环境要求

- Python >= 3.12
- PostgreSQL >= 12
- Neo4j >= 5.0
- Redis (可选，用于缓存)

### 安装依赖

推荐使用 `uv` 进行依赖管理：

```bash
# 安装 uv (如果未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv sync
```

或使用 pip:

```bash
pip install -e .
```

### 配置

1. **复制环境变量配置文件**

```bash
cp .env.example .env
```

2. **编辑 `.env` 文件，配置 LLM 相关参数**

```env
# LLM 主模型配置
LLM_MODEL_NAME=gpt-3.5-turbo
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_openai_api_key_here

# LLM 备用模型配置
BACKUP_LLM_MODEL_NAME=gpt-3.5-turbo
BACKUP_LLM_BASE_URL=https://api.openai.com/v1
BACKUP_LLM_API_KEY=your_backup_openai_api_key_here

# 工作流配置
WORKFLOW_MAX_STEPS=10
WORKFLOW_ENABLE_MEMORY=true
WORKFLOW_LOG_LEVEL=INFO

# React Agent 配置
REACT_MAX_ITERATIONS=5
REACT_TOOL_TIMEOUT=30
```

3. **编辑 `etc/config.yaml` 配置文件**

```yaml
# 基础设置
project_name: "Terra AIOps Platform"
api_v1_str: "/api/v1"
http_host: "0.0.0.0"
http_port: 7082

# CORS 配置
backend_cors_origins: ["http://localhost:3000"]

# PostgreSQL 数据库配置
postgres:
  server: "localhost"
  port: 5432
  user: "your_user"
  password: "your_password"
  db: "terra-aiops"
  pool_size: 20
  max_overflow: 30

# Neo4j 配置
neo4j:
  url: "bolt://localhost:7687"
  user: "neo4j"
  password: "your_neo4j_password"

# 日志配置
logging:
  level: "INFO"
  dir: "logs"
  sql_debug: false

# 缓存配置
cache:
  type: "memory"  # memory 或 redis
  max_size: 1000
```

### 数据库初始化

```bash
# 运行数据库迁移
alembic upgrade head
```

### 启动服务

```bash
# 开发模式（自动重载）
python main.py

# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 7082 --reload
```

服务将在 `http://localhost:7082` 启动。

## API 文档

启动服务后，访问以下地址查看自动生成的 API 文档：

- **Swagger UI**: http://localhost:7082/api/v1/docs
- **ReDoc**: http://localhost:7082/api/v1/redoc
- **OpenAPI JSON**: http://localhost:7082/api/v1/openapi.json

## API 模块

### SDN 控制器管理 `/api/v1/sdn`

- `POST /controllers` - 创建 SDN 控制器
- `GET /controllers` - 列出所有控制器
- `GET /controllers/{id}` - 获取控制器详情
- `PUT /controllers/{id}` - 更新控制器配置
- `DELETE /controllers/{id}` - 删除控制器
- `POST /controllers/{id}/test` - 测试连接
- `GET /controllers/{id}/topology` - 获取拓扑
- `GET /controllers/{id}/sync_topology` - 同步拓扑到图数据库
- `GET /controllers/{id}/monitoring` - 获取监控数据
- `GET /controllers/{id}/logs` - 获取日志
- `GET /snapshots` - 列出拓扑快照
- `GET /snapshots/{id}` - 获取快照详情
- `DELETE /snapshots/{id}` - 删除快照

### MCP 服务器管理 `/api/v1/mcp`

- `POST /servers` - 添加 MCP 服务器
- `GET /servers` - 列出所有 MCP 服务器
- `GET /servers/{id}` - 获取服务器详情
- `PUT /servers/{id}` - 更新服务器配置
- `DELETE /servers/{id}` - 删除服务器
- `GET /{server_id}/tools` - 获取可用工具列表
- `POST /{server_id}/tools/call` - 调用工具

### 图数据库管理 `/api/v1/graph/database`

- Neo4j 图谱查询和管理接口

### 图谱位置管理 `/api/v1/graph/position`

- 图谱节点位置保存和查询

## 开发指南

### 添加新的 API 端点

1. 在 `apps/models/service/` 中定义数据模型
2. 在 `apps/service/` 中实现业务逻辑
3. 在 `apps/router/` 中创建路由
4. 在 `apps/api.py` 中注册路由

### 数据库迁移

```bash
# 创建新的迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest test/unit/

# 运行集成测试
pytest test/integration/
```

## 部署

### 生产环境配置

1. 修改 `etc/config.yaml` 中的生产配置
2. 使用生产级别的 WSGI 服务器（如 Gunicorn）

```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:7082 \
  --log-level info
```

### Docker 部署

```dockerfile
# 示例 Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装 uv
RUN pip install uv

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装依赖
RUN uv sync --frozen

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 7082

# 启动服务
CMD ["python", "main.py"]
```

## 日志

日志文件存储在 `logs/` 目录下，可在 `etc/config.yaml` 中配置日志级别和格式。

## 许可证

[添加许可证信息]

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

[添加联系方式]
