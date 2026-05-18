-- MySQL 数据库创建脚本
-- 用于手动创建数据库（如果自动创建失败）

-- 创建数据库
CREATE DATABASE IF NOT EXISTS test_openai 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE test_openai;

-- 查看数据库信息
SHOW DATABASES LIKE 'test_openai';

-- 可选：创建专用用户（生产环境推荐）
-- CREATE USER 'test_openai_user'@'localhost' IDENTIFIED BY 'your_secure_password';
-- GRANT ALL PRIVILEGES ON test_openai.* TO 'test_openai_user'@'localhost';
-- FLUSH PRIVILEGES;

