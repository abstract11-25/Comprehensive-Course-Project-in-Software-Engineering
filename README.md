# 智能体评估系统 - 运行指南

## 📋 环境要求

### 后端
- **Python**: 3.8 或更高版本
- **pip**: Python 包管理器

### 前端
- **Node.js**: 20.19.0 或更高版本（或 22.12.0+）
- **npm**: Node.js 包管理器

## 🚀 快速开始

### 方法一：使用启动脚本（Windows）

1. **双击运行 `start.bat`**
   - 脚本会自动启动后端和前端服务
   - 首次运行需要先完成下面的环境配置

### 方法二：手动启动

#### 第一步：配置后端环境

1. **进入后端目录**
```bash
cd BackEnd
```

2. **创建虚拟环境（推荐）**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

> ⚠️ **注意**：首次安装可能需要较长时间，因为需要下载 PyTorch 和 sentence-transformers 等大型依赖包。

4. **启动后端服务**
```bash
uvicorn main:app --reload
```

后端服务将在 `http://127.0.0.1:8000` 启动

#### 第二步：配置前端环境

1. **打开新的终端窗口，进入前端目录**
```bash
cd FrontEnd
```

2. **安装依赖**
```bash
npm install
```

3. **启动前端服务**
```bash
npm run dev
```

前端服务将在 `http://127.0.0.1:5173` 启动

## 🌐 访问系统

1. **打开浏览器访问**: http://127.0.0.1:5173
2. **首次使用**：
   - 系统会自动跳转到登录页面
   - 点击"注册"标签页创建新账号
   - 注册成功后切换到"登录"标签页登录
   - 登录后即可使用评估功能

## 📝 使用说明

### 1. 注册账号
- 在登录页面点击"注册"标签
- 填写用户名、邮箱、密码（至少6位）
- 点击"注册"按钮

### 2. 登录系统
- 使用注册的用户名或邮箱登录
- 登录状态会自动保存，刷新页面无需重新登录

### 3. 使用评估功能
- 登录后进入评估页面
- 输入智谱AI的API密钥
- 选择测试用例来源（默认或自定义）
- 选择评估类型（功能评估/安全评估）
- 点击"开始评估"按钮

## 🔧 常见问题

### 后端问题

**Q: 安装依赖时出错，提示找不到某些包**
```bash
# 解决方案：升级pip
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Q: 启动后端时提示端口被占用**
```bash
# 解决方案：修改端口
uvicorn main:app --reload --port 8001
```

**Q: 数据库文件在哪里？**
- 数据库文件会自动创建在 `BackEnd/users.db`
- 首次运行会自动创建用户表

### 前端问题

**Q: npm install 很慢或失败**
```bash
# 解决方案：使用国内镜像
npm config set registry https://registry.npmmirror.com
npm install
```

**Q: 前端无法连接后端**
- 检查后端是否已启动（访问 http://127.0.0.1:8000/docs 查看API文档）
- 检查 `FrontEnd/src/utils/request.ts` 中的 baseURL 是否正确

**Q: 登录后提示 token 无效**
- 清除浏览器缓存和 localStorage
- 重新登录

### 其他问题

**Q: 评估功能无法使用**
- 确保已登录系统
- 检查智谱AI API密钥是否正确
- 查看浏览器控制台和后端日志的错误信息

## 📁 项目结构

```
testOpenAI/
├── BackEnd/              # 后端代码
│   ├── main.py          # FastAPI主服务
│   ├── AI_Agent.py      # AI评估核心逻辑
│   ├── auth.py          # 认证模块
│   ├── database.py      # 数据库模型
│   ├── requirements.txt # Python依赖
│   └── users.db         # SQLite数据库（自动创建）
├── FrontEnd/            # 前端代码
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   ├── stores/      # 状态管理
│   │   ├── router/      # 路由配置
│   │   └── utils/       # 工具函数
│   └── package.json     # Node.js依赖
└── start.bat           # 一键启动脚本（Windows）
```

## 🔐 安全提示

1. **生产环境部署前**：
   - 修改 `BackEnd/auth.py` 中的 `SECRET_KEY` 为强随机密钥
   - 使用环境变量管理敏感信息
   - 配置 HTTPS

2. **API密钥安全**：
   - 不要将API密钥提交到代码仓库
   - 使用环境变量或配置文件管理

## 📚 API文档

后端启动后，可以访问以下地址查看API文档：
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 🛠️ 开发模式

### 后端热重载
后端已配置 `--reload` 参数，修改代码后会自动重启

### 前端热重载
前端使用 Vite，修改代码后会自动刷新浏览器

## 📞 技术支持

如遇到问题，请检查：
1. 控制台错误信息
2. 后端日志输出
3. 浏览器开发者工具的网络请求

---

**祝使用愉快！** 🎉

