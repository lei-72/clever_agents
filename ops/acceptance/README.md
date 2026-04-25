## 阶段14（联调）交付验收与回归步骤

本文档用于 **端到端联调回归** 与 **交付验收**（前端 Vue3 + 后端 FastAPI + Orchestrator/Agents）。

### 1. 环境前置

- **Python**: 3.11+（已在 3.12 验证通过）
- **Node.js**: 18+（已在 Node 22 / npm 11 验证通过）

### 2. 后端启动（FastAPI）

在仓库根目录执行：

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

若 8000 端口被占用，可替换为其它端口（例如 8088）。

### 3. 前端启动（开发模式）

在 `frontend/` 目录执行：

```bash
npm install
npm run dev
```

### 4. 前端构建（交付产物）

在 `frontend/` 目录执行：

```bash
npm run build
```

### 5. 冒烟回归（推荐顺序）

#### 5.1 基础连通性

- `GET /`：服务根路径返回 message
- `GET /metrics`：Prometheus 指标（可选）

#### 5.2 系统健康检查（必须）

- `GET /api/v1/system/health`
- `GET /api/v1/system/ready`

#### 5.3 Orchestrator 路由与流式（必须）

- `POST /api/v1/orchestrator/route`
- `POST /api/v1/orchestrator/stream`（SSE 事件顺序应为 `route -> delta -> done`）

#### 5.4 Orchestrator 执行（建议）

- `POST /api/v1/orchestrator/execute`
- `POST /api/v1/orchestrator/pipeline/execute`（会依赖真实 LLM/MCP 配置；无外部依赖场景建议用测试覆盖验证）

### 6. 回归用请求集合（HTTP Client）

仓库根目录提供了 `test_main.http`，覆盖：

- System health/ready
- Orchestrator route/stream/execute/pipeline
- QA ingest/ask/ingest-file
- Resume review
- Interview start/answer/report
- Grading grade/review-publish

使用 VSCode/Cursor 的 REST Client 打开并逐段执行即可。

### 7. 自动化回归（CI/本地）

在仓库根目录执行：

```bash
python -m pytest -q
```

说明：

- `tests/test_orchestrator_execute_pipeline_integration.py` 提供了编排流水线的集成级回归。

