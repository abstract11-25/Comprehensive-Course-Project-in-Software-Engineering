# 智能体评估系统开发指南

> 本指南面向新加入的开发者与运维人员，帮助你在最短时间内理解项目架构、完成环境搭建、掌握开发流程并安全地部署到生产环境。

---

## 目录
- [项目概览与核心能力](#项目概览与核心能力)
- [系统架构总览](#系统架构总览)
- [后端（FastAPI）详细说明](#后端fastapi详细说明)
- [前端（Vue3 + Element Plus）说明](#前端vue3--element-plus说明)
- [开发环境准备与依赖管理](#开发环境准备与依赖管理)
- [本地运行与调试流程](#本地运行与调试流程)
- [数据库与外部服务配置](#数据库与外部服务配置)
- [部署与运维建议](#部署与运维建议)
- [测试策略与质量保障](#测试策略与质量保障)
- [常见问题与排障](#常见问题与排障)
- [贡献指南与团队流程](#贡献指南与团队流程)

---

## 项目概览与核心能力
- **项目名称**：智能体评估系统 `testOpenAI`
- **目标**：对接主流大模型接口（默认兼容智谱、OpenAI 及其他 OpenAI-Style API），对代理回答进行功能性与安全性评估，并为内部测试团队提供可视化操作界面。
- **亮点能力**
  - 支持默认测试集与自定义 JSON 测试用例。
  - 功能性评估使用 `sentence-transformers` 计算语义相似度，安全评估检测敏感关键字。
  - 支持长任务异步执行，实时进度轮询与任务取消。
  - 完整的用户认证体系（注册、登录、token 鉴权）。
  - 内置智能体工厂，可按需自助切换或增加 LLM 服务商，无需改动后端代码。
- **用户角色**
  - 普通用户：注册后即可发起评估、查看结果。
  - 未来可选：管理员（管理测试用例、查看全局统计等）。

---

## 系统架构总览
```
┌──────────┐      HTTPS       ┌────────┐
│  前端     │  ─────────────▶ │  后端   │
│ (Vue3)   │ ◀─────────────  │ FastAPI │
└──────────┘   JSON (REST)   └────────┘
      │                          │
      │ Axios                    │ SQLAlchemy
      ▼                          ▼
┌──────────┐             ┌──────────────────┐
│ 用户浏览器 │             │ 数据库 (MySQL/SQLite) │
└──────────┘             └──────────────────┘
                                  │
                                  │ requests
                                  ▼
                         ┌───────────────────────┐
                         │ LLM Provider API       │
                         │ (Zhipu / OpenAI / …)   │
                         └───────────────────────┘
```

- **通信方式**：前后端分离，使用 RESTful API；认证基于 JWT Bearer Token。
- **任务执行流程**
  1. 用户登录后在前端提交评估请求。
  2. 后端创建任务，交给 `AgentFactory` 生成对应供应商的智能体客户端。
  3. 对响应进行事实性和安全性评估，累积到任务结果中。
  4. 前端通过轮询接口获取任务进度，支持随时取消。
- **关键依赖**
  - 后端：FastAPI、SQLAlchemy、python-jose、sentence-transformers。
  - 前端：Vue3、Vite、Pinia、Element Plus、Axios。

---

## 后端（FastAPI）详细说明

### 代码结构
```
BackEnd/
├── main.py           # FastAPI 入口、路由定义
├── AI_Agent.py       # 智谱 API 封装与评估逻辑
├── auth.py           # JWT 与密码哈希
├── database.py       # SQLAlchemy 配置与 User 模型
├── requirements.txt  # Python 依赖
└── test_cases.json   # 默认测试集
```

### 入口与路由
- `BackEnd/main.py`
  - 初始化 FastAPI 应用与 CORS。
  - 调用 `init_db()` 确保数据库表存在。
  - 提供以下核心路由：
    - `POST /api/auth/register`：用户注册。
    - `POST /api/auth/login`：用户登录，返回 JWT。
    - `GET /api/auth/me`：获取当前用户信息。
    - `POST /api/evaluate`：启动评估任务（需鉴权）。
    - `GET /api/evaluation/{task_id}`：查询任务进度。
    - `POST /api/cancel/{task_id}`：取消正在执行的任务。

### 认证与安全
- `auth.py`
  - 使用 `passlib[bcrypt]` 加密密码，函数 `get_password_hash` 与 `verify_password`。
  - JWT 由 `create_access_token` 签发，默认有效期 30 天。
  - `get_current_user` 作为 FastAPI 依赖，保护需要登录的路由。
  - **生产环境注意**：将 `SECRET_KEY` 替换为随机强密钥，并使用环境变量管理。

### 数据访问层
- `database.py`
  - 默认使用 SQLite 数据库（`BackEnd/users.db`），可通过设置环境变量 `DB_DRIVER=mysql` 切换到 MySQL。
  - 若使用 MySQL，请提前安装 `pymysql` 并配置 `DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME` 等环境变量。
  - `User` 模型字段：`id`, `username`, `email`, `hashed_password`, `created_at`。
  - `init_db()` 创建所有表，`get_db()` 对请求范围提供数据库会话。

### 评估核心逻辑
- `AI_Agent.py`
  - `AgentSettings` 统一描述供应商、API Key、模型、超时等配置，支持附加 Header/Body。
  - `AgentFactory.create(settings)` 根据 `provider` 返回 `ZhipuAgent` 或 `OpenAICompatibleAgent`，兼容智谱与 OpenAI Chat Completions 标准。
  - `AgentEvaluator` 默认从 `BackEnd/test_cases.json` 读取用例，也可被前端覆盖。
  - 功能评估通过 `FactualityEvaluator` 调用 `SentenceTransformer("shibing624/text2vec-base-chinese")` 计算语义相似度（阈值 0.5，支持模型缓存）。
  - 安全评估采用关键词匹配，比较实际回答中是否含期望拒绝语句。
  - 关键参数：
    - `timeout` 默认 60 秒，可按供应商需求在请求体中传入。
    - `max_retries` 默认 2 次，支持定制。
    - 前端轮询接口默认 1 秒更新一次。

### 任务管理
- 在 `main.py` 中维护 `evaluation_tasks` 字典，结构：
  ```python
  evaluation_tasks: Dict[str, Tuple[Dict, asyncio.Event]]
  ```
  - `Dict` 保存任务状态（进度、当前用例、结果列表、总结）。
  - `asyncio.Event` 用于任务取消。
- `run_evaluation()` 异步函数负责遍历测试用例、调用模型、更新状态。
  - 每条测试用例外层还有 `asyncio.wait_for(..., timeout=90)`，防止卡死。
  - 任务完成后生成总结，包括功能准确率、安全通过率、总耗时。

### 特征评估指标
- 后端在 `run_evaluation()` 完成后会调用 `FeatureMetricsCalculator`，根据任务结果与用例元数据生成 `summary["feature_metrics"]`：
  - **基础指标**：准确率、召回率、F1 值、任务完成率、平均响应耗时、累计用例数。
  - **适应性**：依赖 `metadata.scene_type`（`train` / `non_train` / `unknown` 等）、`metadata.is_unknown_scene`、`metadata.adaptation_time` 统计跨场景偏差、覆盖度与未知场景适配耗时。
  - **鲁棒性**：通过 `metadata.abnormal_input`、`metadata.high_concurrency`、`metadata.environment_unstable` 记录异常输入错误率、高并发稳定性、环境波动容错率。
  - **可移植性**：读取 `metadata.deployment_attempt`、`metadata.deployment_success`、`metadata.compatibility_issues`、`metadata.compatibility_coverage`、`metadata.adaptation_cost` 评估跨环境部署成功率和适配成本系数。
  - **协作效率**：根据 `metadata.collaboration`、`metadata.collaboration_duration`、`metadata.single_agent_baseline`、`metadata.contribution_ratio`、`metadata.contribution_weight` 计算信息交互准确率、协作耗时差值、贡献度。
- 请求体中的 `feature_config` 可配置基准值：
  ```json
  {
    "feature_config": {
      "enabled": true,
      "ground_truth_total": 120,
      "total_scene_types": 8,
      "baseline_single_task_time": 12.5,
      "baseline_adaptation_cost": 1.0,
      "features": ["basic", "adaptivity", "robustness", "portability", "collaboration"]
    }
  }
  ```
  留空时根据测试结果自动推断。
- 自定义测试集支持为每条用例添加 `metadata` 字段，示例见 `BackEnd/test_cases.json`：
  ```json
  {
    "type": "functional",
    "input": "...",
    "expected": "...",
    "category": "...",
    "metadata": {
      "scene_type": "non_train",
      "high_concurrency": true,
      "deployment_attempt": true,
      "deployment_success": false,
      "compatibility_issues": 2,
      "compatibility_coverage": 0.6,
      "adaptation_cost": 1.4
    }
  }
  ```
  未提供元数据时，对应指标返回 `null`（前端会隐藏该项）。

### 智能体接入与 API 配置
- `POST /api/evaluate` 支持两种写法：
  1. 直接在根节点传参数（兼容旧版）：
     ```json
     {
       "provider": "zhipu",
       "api_key": "xxxx",
       "model": "glm-4.5-flash",
       "evaluation_types": ["functional", "safety"]
     }
     ```
  2. 通过 `agent` 对象传完整配置（推荐）：
     ```json
     {
       "agent": {
         "provider": "openai",
         "api_key": "sk-***",
         "model": "gpt-4o-mini",
         "base_url": "https://api.openai.com/v1/chat/completions",
         "temperature": 0.2,
         "extra_headers": {},
         "extra_body": {}
       },
       "evaluation_types": ["functional"]
     }
     ```
- 供应商说明：
  - `zhipu`：默认访问 `https://open.bigmodel.cn/api/paas/v4/chat/completions`。
  - `openai`、`deepseek`、`moonshot`、`qwen/dashscope`、`yi`、`baichuan` 等均复用 OpenAI Chat Completions 格式，可通过修改 `base_url`/`model` 切换。
  - 其他 OpenAI 兼容平台（如自建 API 网关）设置 `provider: "openai-compatible"` 或 `custom`，并提供 `base_url` 与 `model` 即可。
  - 特殊认证方式（如 Azure OpenAI 需 `api-key` 头）可通过 `extra_headers` 或 `extra_body` 自定义。
- 任务状态中会记录 `agent.provider/model/base_url`，方便前端或运维排查具体使用的模型。
- 若需要新增完全不同的协议，可在 `AI_Agent.AgentFactory` 中扩展新的 Client 类，无需改动其他业务逻辑。

### 错误处理建议
- 捕获 `HTTPException` 并返回合理的状态码与提示。
- 外部 API 错误时将详细信息写入 `task_status["current_response"]` 以便前端展示。
- 若部署在多进程环境，请将任务状态持久化（例如 Redis）；当前实现仅适合单进程部署。

---

## 前端（Vue3 + Element Plus）说明

### 目录结构
```
FrontEnd/
├── src/
│   ├── main.ts               # 应用入口，注册 Pinia 与路由
│   ├── router/index.ts       # 路由守卫，未登录自动跳转
│   ├── stores/user.ts        # 用户认证状态，读写 localStorage
│   ├── utils/request.ts      # Axios 实例，处理鉴权与错误提示
│   └── views/
│       ├── LoginView.vue     # 登录/注册页
│       └── EvaluationView.vue# 评估主界面
└── package.json
```

### 核心组件
- `LoginView.vue`
  - Element Plus 表单与校验规则，支持标签页切换登录/注册。
  - 注册错误时展示详细提示，并指导用户更正。
- `EvaluationView.vue`
  - 包含评估配置、进度展示、结果表格与取消按钮。
  - 表单支持选择服务商、填写模型/Base URL，并可调整温度、Max Tokens、超时及额外 Header/Body，以与后端的 `AgentFactory` 对应。
  - “特征评估配置”开关用于装配 `feature_config`（真实正例数量、场景总数、协同基准耗时、适配成本基准）。
  - 通过 `request.post('/api/evaluate')` 发起任务，并使用 `setInterval` 轮询状态；提交时会组装 `agent` 对象及可选 `feature_config` 实现自助扩展。
  - 结果区域新增“基础特征指标”“通用化指标”卡片，展示后端返回的特征评估结果。
  - 状态字段映射：
    - `progress`（0-100）
    - `current_case`、`current_input`、`current_response`
    - `results`（列表，包含功能/安全类型、期望值、实际值、是否通过）
    - `summary`（任务完成后统计）
- `stores/user.ts`
  - 登录后调用 `setAuth()` 保存 token 与用户信息到 localStorage。
  - 初始化时 `restoreAuth()` 自动恢复状态。
  - `fetchUserInfo()` 请求 `/api/auth/me` 验证 token 有效性。
- `utils/request.ts`
  - Axios 请求拦截器自动带上 `Authorization: Bearer <token>`。
  - 响应拦截器在 401 时清除认证信息并跳转登录页。

### UI 与交互注意事项
- 评估进行中禁用“开始评估”按钮，避免重复提交。
- 取消任务后，前端立即停止轮询，防止重复请求已取消的任务。
- 默认 `baseURL` 写死为 `http://127.0.0.1:8000`，生产环境需使用环境变量替换（见部署章节）。

---

## 开发环境准备与依赖管理

### 基础要求
- 操作系统：Windows 10+/macOS/Linux（开发环境）
- Python：3.8+
- Node.js：建议 `20.19.0` 或 `22.12.0` 及以上
- npm：随 Node 安装，建议使用 `npm` 或 `pnpm`

### 后端依赖
```bash
cd BackEnd
python -m venv .venv      # 推荐创建虚拟环境
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Linux / macOS
pip install -r requirements.txt
```

`requirements.txt` 已锁定部分关键版本，避免与 `torch`、`transformers` 不兼容。首次安装会下载较大的模型依赖，建议预留充足时间或使用国内镜像源。

### 前端依赖
```bash
cd FrontEnd
npm install
```

若 `npm install` 较慢，可切换镜像：
```bash
npm config set registry https://registry.npmmirror.com
```

### 环境变量与敏感信息
- 智谱 AI API Key 不写入仓库，建议在运行脚本或环境变量中设置。
- 数据库凭据、JWT `SECRET_KEY` 放入 `.env` 或运行时配置。
- 针对 Windows 的一键启动脚本 `start.bat` 默认读取本地配置，请根据实际情况调整。

---

## 本地运行与调试流程

### 启动方式一：手动启动
```bash
# 终端 1 - 后端
cd BackEnd
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 终端 2 - 前端
cd FrontEnd
npm run dev -- --host 0.0.0.0 --port 5173
```
- 访问地址：`http://127.0.0.1:5173`
- 后端交互文档：`http://127.0.0.1:8000/docs`

### 启动方式二：Windows 一键脚本
- 双击 `start.bat`，脚本会在新窗口分别启动后端与前端。
- **首次执行前** 仍需手动完成依赖安装。

### 调试建议
- **后端**
  - 使用 Swagger UI 测试 `register/login`、`evaluate` 接口。
  - `uvicorn --reload` 支持热重载，日志中可查看任务执行详情。
  - 对外部 API 调用可使用环境变量 `ZHIPU_API_KEY` 传入，便于切换。
- **前端**
  - Vite 默认启用热更新，调整组件后刷新浏览器。
  - 使用浏览器开发者工具 Network 面板查看轮询请求。
  - 如需要代理跨域，可在 `vite.config.ts` 中配置 `server.proxy`。

### 评估任务调试技巧
- 默认测试集位于 `BackEnd/test_cases.json`，可直接编辑。
- 自定义测试集需要 `type`、`input`、`expected`、`category` 字段。
- 观察任务状态字段：
  - `progress`：任务进度百分比。
  - `current_response`：最近一次模型返回（截断）。
  - `results`：累计结果，可用于排查评估逻辑问题。
- 若任务一直在“运行中”，检查外部 API 是否超时或密钥是否有效。

---

## 数据库与外部服务配置

### 数据库
- **默认配置**：MySQL，连接串读取以下环境变量
  - `DB_HOST`（默认 127.0.0.1）
  - `DB_PORT`（默认 3306）
  - `DB_USER`（默认 root）
  - `DB_PASSWORD`（默认空字符串）
  - `DB_NAME`（默认 test_openai，需要提前创建数据库）
- 若仅在本地快速验证，可切换为 SQLite：
  ```python
  SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"
  ```
  切换后请删除 MySQL 相关依赖或保持环境变量为空，避免误连。

### 外部服务：智谱 AI API
- 接口地址：`https://open.bigmodel.cn/api/paas/v4/chat/completions`
- 默认模型：`glm-4.5-flash`
- 请求参数：
  ```json
  {
    "model": "glm-4.5-flash",
    "messages": [{"role": "user", "content": "<prompt>"}],
    "temperature": 0.3,
    "max_tokens": 512
  }
  ```
- 安全注意事项
  - 将 API Key 储存在环境变量或密钥管理服务中。
  - 失败时 `generate_response` 返回错误信息，前端需识别并提示用户。
  - 若频繁超时，可调高 `timeout` 或减少并发任务数。

---

## 部署与运维建议

### 推荐拓扑
1. **前端**：构建后部署到静态资源服务器（Nginx、CDN）。
2. **后端**：使用 `uvicorn` 或 `gunicorn` + `uvicorn.workers.UvicornWorker` 部署在 Linux 服务器（建议使用进程管理器如 `systemd` 或 `supervisor`）。
3. **数据库**：托管在云数据库或自建 MySQL。
4. **HTTPS**：在 Nginx 层启用 TLS，并配置反向代理到后端。

### 关键配置
- 设置环境变量：
  ```bash
  export SECRET_KEY="<随机密钥>"
  export DB_USER="<db_user>"
  export DB_PASSWORD="<db_password>"
  export ZHIPU_API_KEY="<api_key>"
  ```
- 生产前端向后端请求时请将 `baseURL` 指向公开域名，可在 `.env.production` 中设置：
  ```
  VITE_API_BASE_URL=https://api.example.com
  ```
  然后在 `utils/request.ts` 中读取 `import.meta.env.VITE_API_BASE_URL`。

### 安全基线
- 强制使用 HTTPS，禁止明文传输 token。
- 将 `allow_origins` 限定为可信域名，避免 `allow_origins=["*"]`。
- 开启日志审计，特别是登录、任务执行、取消操作。
- 定期轮换 API Key / JWT 密钥，密码使用强加密。

### 运维监控
- FastAPI 日志：关注任务失败、超时、未处理异常。
- 资源监控：评估任务可能触发外部 API 限流，建议监控请求速率。
- 告警：连续任务失败、JWT 认证失败数量异常增加时需要通知。

---

## 测试策略与质量保障

### 单元测试（建议）
- 使用 `pytest` + `httpx` 对下列模块编写测试：
  - 认证逻辑：密码哈希、token 生成与解析。
  - 评估逻辑：`FactualityEvaluator.evaluate`、安全关键词匹配。
  - API 层：模拟请求 `POST /api/auth/register/login`，校验返回值。

### 集成测试
- 使用 SQLite 和假 API Key 启动一个最小化环境。
- 通过前端或 Postman 跑完整的注册 -> 登录 -> 评估流程。
- Mock 智谱 API 响应，验证不同返回值下的评估结果。

### 回归与数据驱动测试
- 保留默认测试集，作为功能基线。
- 针对新增功能或修复缺陷，添加对应用例到自定义 JSON 中，并记录评估结果。
- 可编写脚本自动读取评估结果，生成准确率报告。

### 性能与稳定性
- 压力测试：使用工具（如 Locust）模拟多个用户同时发起评估，观察队列和外部 API 超时情况。
- 超时策略：根据实际情况调整 `timeout` 与 `max_retries`，防止任务长时间挂起。
- 并发执行：当前实现不持久化任务状态，如需水平扩展需改造为分布式存储。

---

## 常见问题与排障

| 问题 | 可能原因 | 排查步骤 |
| ---- | -------- | -------- |
| `pip install` 安装失败 | 科学计算库下载缓慢 | 使用镜像：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple` |
| 启动后端报错 `SECRET_KEY` | 未设置环境变量 | 在生产环境导出 `SECRET_KEY`，或直接修改 `auth.py` |
| 登录后立即跳回登录页 | token 进入请求头失败 | 检查 `utils/request.ts` 是否正确注入 `Authorization` |
| 评估任务一直 0% | 外部 API 密钥无效/超时 | 查看后端日志，确认 `ZhipuAgent` 返回内容 |
| `sqlite3.OperationalError` | 未创建数据库 | 切换 MySQL 时需提前建库；SQLite 检查文件权限 |
| 前端显示 `token 无效` | localStorage 遗留旧 token | 清理浏览器缓存或调用 `userStore.clearAuth()` |
| 自定义测试集无法解析 | JSON 格式不正确 | 使用 JSON 校验工具；确保包含 `type/input/expected/category` |

---

## 贡献指南与团队流程

### 分支策略
- `main`：稳定分支，随时可部署。
- `develop`（可选）：集成测试分支。
- 功能分支：`feature/<short-description>`。
- 修复分支：`fix/<issue-id>`。
- 每个分支需从最新的 `main/develop` 拉取。

### 代码风格
- **Python**
  - 遵循 PEP 8，推荐使用 `ruff` 或 `flake8` 自动检查。
  - 类型标注使用 `typing` 与 `pydantic`，提升 IDE 体验。
  - 异步函数需关注 `await` 的正确使用，避免阻塞事件循环。
- **TypeScript / Vue**
  - 遵循 ESLint + Prettier 配置（可在项目中补充 `.eslintrc.cjs`/`.prettierrc`）。
  - 组件命名使用 PascalCase，Pinia store 使用 camelCase。
  - API 调用统一封装在 `utils/request.ts`。

### 提交流程
1. 创建分支并实现功能。
2. 本地运行后端与前端基础测试（确保能注册、登录、完成一轮评估）。
3. 运行自定义或默认测试集，记录结果。
4. 提交代码：
   ```bash
   git add .
   git commit -m "feat: <summary>"
   git push origin feature/<summary>
   ```
5. 发起 Pull Request：
   - 描述变更、影响面的模块、测试情况。
   - 若涉及依赖变更，说明安装步骤。
6. 通过代码评审后合并。

### 代码评审要点
- 是否涉及敏感配置（SECRET_KEY、API Key），避免明文提交。
- 后端是否正确处理异常、返回的状态码合理。
- 前端是否对错误进行了用户提示，避免静默失败。
- 文档是否同步更新（README / 本开发指南）。

### 发布与回滚
- 合并到 `main` 后，运行构建与部署脚本。
- 部署前确认环境变量、依赖版本等。
- 若出现严重问题，使用 Git 回滚到上一个稳定版本：
  ```bash
  git revert <commit_hash>
  ```
- 部署回滚需同步处理数据库迁移（如有）、缓存刷新。

---

## 附录
- **默认端口**：后端 `8000`、前端 `5173`
- **外部文档**：
  - [FastAPI 官方文档](https://fastapi.tiangolo.com/)
  - [Vue 3 官方文档](https://cn.vuejs.org/)
  - [Element Plus 组件库](https://element-plus.org/zh-CN/)
  - [智谱 AI API 文档](https://open.bigmodel.cn/)

---

> 如需进一步帮助，请优先查看仓库根目录 `README.md`、`BackEnd/README_AUTH.md`，或联系项目维护者。欢迎持续完善本文档。谢谢！

