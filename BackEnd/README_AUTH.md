# 用户认证功能说明

## 功能概述

已为智能体评估系统添加完整的用户登录/注册功能，包括：

1. **用户注册**：新用户可以注册账号
2. **用户登录**：使用用户名/邮箱和密码登录
3. **JWT认证**：使用JWT token进行身份验证
4. **路由保护**：评估接口需要登录后才能访问
5. **自动登录**：token保存在localStorage，刷新页面自动恢复登录状态

## 数据库

系统使用SQLite数据库存储用户信息，数据库文件为 `users.db`（自动创建）。

## API接口

### 1. 用户注册
- **URL**: `POST /api/auth/register`
- **请求体**:
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}
```

### 2. 用户登录
- **URL**: `POST /api/auth/login`
- **请求格式**: FormData (OAuth2标准)
- **参数**:
  - `username`: 用户名或邮箱
  - `password`: 密码
- **响应**:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

### 3. 获取当前用户信息
- **URL**: `GET /api/auth/me`
- **认证**: 需要Bearer token
- **响应**:
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "created_at": "2024-01-01T00:00:00"
}
```

## 安全说明

1. **密码加密**：使用bcrypt加密存储密码
2. **JWT Token**：token有效期30天
3. **生产环境**：请修改 `auth.py` 中的 `SECRET_KEY` 为强随机密钥

## 安装依赖

```bash
cd BackEnd
pip install -r requirements.txt
```

## 启动服务

使用 `start.bat` 或手动启动：

```bash
# 后端
cd BackEnd
uvicorn main:app --reload

# 前端
cd FrontEnd
npm run dev
```

## 使用流程

1. 访问前端页面（默认 http://127.0.0.1:5173）
2. 系统会自动跳转到登录页面（如果未登录）
3. 点击"注册"标签页创建新账号
4. 注册成功后切换到"登录"标签页登录
5. 登录成功后可以访问评估功能

