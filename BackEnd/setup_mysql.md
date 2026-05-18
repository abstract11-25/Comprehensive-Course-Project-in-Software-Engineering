# MySQL 数据库配置指南

## 一、安装 MySQL

### Windows 系统
1. 下载 MySQL Installer: https://dev.mysql.com/downloads/installer/
2. 选择 "MySQL Server" 和 "MySQL Workbench"（可选，用于图形化管理）
3. 安装过程中设置 root 用户密码（请记住这个密码）

### Linux 系统
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server

# CentOS/RHEL
sudo yum install mysql-server
```

### macOS 系统
```bash
# 使用 Homebrew
brew install mysql
brew services start mysql
```

## 二、创建数据库

### 方法1：使用命令行（推荐）

1. 登录 MySQL：
```bash
mysql -u root -p
# 输入 root 密码
```

2. 创建数据库：
```sql
CREATE DATABASE test_openai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. 创建专用用户（可选，推荐用于生产环境）：
```sql
-- 创建用户
CREATE USER 'test_openai_user'@'localhost' IDENTIFIED BY 'Wzx112500!';

-- 授予权限
GRANT ALL PRIVILEGES ON test_openai.* TO 'test_openai_user'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 退出
EXIT;
```

### 方法2：使用 MySQL Workbench

1. 打开 MySQL Workbench
2. 连接到本地 MySQL 服务器
3. 在 Query 窗口中执行：
```sql
CREATE DATABASE test_openai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 三、配置环境变量

### Windows 系统

创建或编辑 `.env` 文件（在 BackEnd 目录下）：

```env
DB_DRIVER=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=Wzx112500!
DB_NAME=test_openai
```

或者使用系统环境变量：
1. 右键"此电脑" -> "属性" -> "高级系统设置" -> "环境变量"
2. 添加以下环境变量：
   - `DB_DRIVER=mysql`
   - `DB_HOST=127.0.0.1`
   - `DB_PORT=3306`
   - `DB_USER=root`
   - `DB_PASSWORD=Wzx112500!`
   - `DB_NAME=test_openai`

### Linux/macOS 系统

在 `BackEnd` 目录创建 `.env` 文件：

```bash
cd BackEnd
cat > .env << EOF
DB_DRIVER=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=test_openai
EOF
```

## 四、安装 Python 依赖

确保已安装 `pymysql`（已在 requirements.txt 中）：

```bash
cd BackEnd
pip install pymysql
```

## 五、测试连接

运行测试脚本：

```bash
python test_mysql_connection.py
```

## 六、启动服务

使用 `start.bat` 或手动启动，系统会自动：
1. 连接到 MySQL 数据库
2. 创建所需的表（users 和 api_keys）

## 七、验证

1. 启动后端服务
2. 访问 http://127.0.0.1:8000/docs
3. 尝试注册一个新用户
4. 检查 MySQL 数据库中是否有数据：

```sql
USE test_openai;
SELECT * FROM users;
SELECT * FROM api_keys;
```

## 常见问题

### 1. 连接被拒绝
- 检查 MySQL 服务是否启动：`mysqladmin -u root -p status`
- 检查防火墙是否阻止了 3306 端口

### 2. 认证失败
- 确认用户名和密码正确
- 检查用户是否有访问数据库的权限

### 3. 字符编码问题
- 确保数据库使用 utf8mb4 字符集
- 检查连接字符串中的 `charset=utf8mb4` 参数

### 4. 表创建失败
- 检查用户是否有 CREATE TABLE 权限
- 查看后端日志中的错误信息

