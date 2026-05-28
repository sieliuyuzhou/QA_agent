# QA_agent 启动指南

## 环境要求

- Python 3.10+
- PostgreSQL 15（Docker 或本地安装）
- Node.js 18+（仅前端需要）
- LLM API 密钥（SiliconFlow / OpenAI 兼容接口）

---

## 一、后端启动

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

推荐使用虚拟环境：

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置环境变量

复制环境变量模板并编辑：

```bash
cp .env.example .env
```

`.env` 文件内容示例：

```ini
LLM_API_KEY=sk-your-key-here
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=deepseek-ai/DeepSeek-V4-Flash
LLM_TIMEOUT=60
LLM_MAX_RETRIES=3

EMBEDDING_API_KEY=sk-your-key-here
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-m3

RAG_PERSIST_DIR=./data/chroma
RAG_COLLECTION_NAME=faq_collection

CONVERSATION_DB_URL=postgresql://user:1234@localhost:5433/agent
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. 启动 PostgreSQL

**方式一：Docker（推荐）**

```bash
docker compose up -d
```

**方式二：本地 PostgreSQL**

确保本地 PostgreSQL 运行在端口 `5433`（或修改 `.env` 中的 `CONVERSATION_DB_URL` 为实际端口）。

验证数据库连接：

```bash
python -c "from infrastructure.database import DatabaseManager; db=DatabaseManager(); db.ping(); print('数据库连接正常')"
```

### 4. 初始化数据库

```bash
python scripts/init_db.py
python scripts/seed_mock_data.py
```

### 5. 启动后端服务

```bash
python main.py
```

启动后终端会显示：

```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

验证服务运行：

```bash
curl http://localhost:8000/health
```

预期返回 `{"status":"ok","checks":{"database":"ok","knowledge_store":"ok"}}`

### 6. 运行测试（可选）

```bash
# 全量回归测试
pytest -q

# 预期输出：194 passed
```

---

## 二、前端启动

前端为 Vue 3 + Vite 项目，用于可视化测试后端能力。

### 1. 安装依赖

```bash
cd frontend_new
npm install
```

### 2. 启动开发服务器

```bash
cd frontend_new
npm run dev
```

启动后终端会显示：

```
VITE v8.x ready in xxx ms
➜  Local:   http://localhost:3000/
```

### 3. 配置代理

前端 Vite 已配置代理，将 `/api` 和 `/health` 请求转发至后端 `http://localhost:8000`。确认 `frontend_new/vite.config.ts` 中包含：

```typescript
server: {
  port: 3000,
  proxy: {
    '/api': { target: 'http://localhost:8000', changeOrigin: true },
    '/health': { target: 'http://localhost:8000', changeOrigin: true }
  }
}
```

### 4. 访问前端

浏览器打开 `http://localhost:3000/`，选择测试用户后即可使用。

---

## 三、测试用户

| 用户 ID | 显示名称 | 角色 | 说明 |
|---------|---------|------|------|
| `customer_alice` | Alice | 普通用户 | 有模拟订单，可测试售后流程 |
| `customer_bob` | Bob | 普通用户 | 有模拟订单，可测试权限隔离 |
| `admin_zhang` | 张管理 | 管理员 | 可访问审计、评测等管理功能 |

---

## 四、测试场景

### 产品咨询

| 输入 | 预期行为 |
|------|---------|
| `X2 支持 Zigbee 吗？` | 返回答案 + 引用来源 |
| `门锁连不上 WiFi` | 反问产品型号 |
| `过保维修怎么收费？` | 返回政策答案 + 引用 |

### 故障排查

```
用户: 门锁连不上 WiFi
智能体: 请问您的门锁型号是什么？
用户: X1
智能体: 给出 X1 的 WiFi 配置排障步骤
```

### 售后办理

```
用户: 我要退货
智能体: 请提供订单号和退货原因
用户: ORD-A-X1
智能体: 请提供退货原因
用户: 质量问题，门锁坏了
智能体: 请确认商品包装是否完好？
用户: 包装完好
智能体: 生成确认按钮 → 用户点击确认 → 创建工单
```

### 转人工

```
用户: 转人工
智能体: 返回 handoff 及转接摘要
```

---

## 五、常见问题

### 数据库连接失败

```
错误: 数据库连接失败，请检查 PostgreSQL 服务是否启动
```

**解决：** 确认 PostgreSQL 已运行且端口正确（`5433`）。使用 `docker ps` 检查容器状态。

### 向量存储连接失败

```
错误: 向量存储连接失败，请检查 ChromaDB 数据目录是否存在
```

**解决：** 确认 `data/chroma/` 目录存在。首次使用需导入 FAQ 数据。

### API 返回 401

```
错误: 缺少内部试用用户标识 / 内部试用用户不可用
```

**解决：** 前端请求需携带 `X-QA-User-Id` 请求头，且用户 ID 需存在于数据库（已通过 `seed_mock_data.py` 导入）。

### LLM 调用超时

```
错误: LLM 响应超时
```

**解决：** 检查 `.env` 中的 `LLM_BASE_URL` 和 `LLM_API_KEY` 配置，或增大 `LLM_TIMEOUT` 值。
