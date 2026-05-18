"""
检查当前使用的数据库类型
"""
import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"[OK] 已加载 .env 文件: {env_path}")
    else:
        print(f"[INFO] .env 文件不存在: {env_path}")
except ImportError:
    print("[INFO] python-dotenv 未安装，跳过 .env 文件加载")

# 读取环境变量
DB_DRIVER = os.getenv("DB_DRIVER", "sqlite").lower()
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "test_openai")
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "users.db"))

print("=" * 60)
print("数据库配置检查")
print("=" * 60)
print(f"\n当前数据库驱动: {DB_DRIVER.upper()}")

if DB_DRIVER == "mysql":
    print("\n[MySQL 配置]")
    print(f"   主机: {DB_HOST}")
    print(f"   端口: {DB_PORT}")
    print(f"   用户: {DB_USER}")
    print(f"   密码: {'*' * len(DB_PASSWORD) if DB_PASSWORD else '(空)'}")
    print(f"   数据库: {DB_NAME}")
    
    # 尝试连接 MySQL
    try:
        import pymysql
        print("\n[测试 MySQL 连接]")
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )
        print("   [OK] MySQL 连接成功")
        
        # 检查表是否存在
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"   [表] 数据库中的表: {[table[0] for table in tables]}")
        
        # 检查用户表
        if ('users',) in tables:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"   [用户] 用户数量: {user_count}")
        
        cursor.close()
        connection.close()
    except ImportError:
        print("   [ERROR] pymysql 未安装")
    except Exception as e:
        print(f"   [ERROR] MySQL 连接失败: {e}")
else:
    print("\n[SQLite 配置]")
    print(f"   数据库文件: {DB_PATH}")
    
    # 检查 SQLite 文件是否存在
    if os.path.exists(DB_PATH):
        file_size = os.path.getsize(DB_PATH)
        print(f"   [OK] 数据库文件存在")
        print(f"   [大小] 文件大小: {file_size} 字节")
        
        # 尝试连接 SQLite
        try:
            import sqlite3
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # 检查表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"   [表] 数据库中的表: {[table[0] for table in tables]}")
            
            # 检查用户表
            if ('users',) in tables:
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                print(f"   [用户] 用户数量: {user_count}")
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"   [ERROR] SQLite 连接失败: {e}")
    else:
        print(f"   [WARN] 数据库文件不存在（首次运行时会自动创建）")

print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)
print("\n[提示]")
print("   - 要切换到 MySQL，创建 .env 文件并设置 DB_DRIVER=mysql")
print("   - 要使用 SQLite，设置 DB_DRIVER=sqlite 或删除 .env 文件")
print("   - 参考 env.example 文件了解配置格式")

