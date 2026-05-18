"""
MySQL 连接测试脚本
用于测试 MySQL 数据库配置是否正确
"""
import os
import sys

# 尝试加载 .env 文件（如果使用 python-dotenv）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 读取环境变量
DB_DRIVER = os.getenv("DB_DRIVER", "sqlite").lower()
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "test_openai")

def test_mysql_connection():
    """测试 MySQL 连接"""
    if DB_DRIVER != "mysql":
        print("[ERROR] 当前配置不是 MySQL，请设置环境变量 DB_DRIVER=mysql")
        return False
    
    try:
        import pymysql
    except ImportError:
        print("[ERROR] 未安装 pymysql，请运行: pip install pymysql")
        return False
    
    print("=" * 50)
    print("MySQL 连接测试")
    print("=" * 50)
    print(f"主机: {DB_HOST}")
    print(f"端口: {DB_PORT}")
    print(f"用户: {DB_USER}")
    print(f"数据库: {DB_NAME}")
    print("-" * 50)
    
    try:
        # 测试连接（不指定数据库，先测试服务器连接）
        print("1. 测试 MySQL 服务器连接...")
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4'
        )
        print("   [OK] MySQL 服务器连接成功")
        connection.close()
        
        # 测试数据库是否存在
        print("2. 测试数据库是否存在...")
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4'
        )
        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
        result = cursor.fetchone()
        
        if result:
            print(f"   [OK] 数据库 '{DB_NAME}' 存在")
        else:
            print(f"   [ERROR] 数据库 '{DB_NAME}' 不存在")
            print(f"   请运行以下 SQL 创建数据库:")
            print(f"   CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cursor.close()
            connection.close()
            return False
        
        cursor.close()
        connection.close()
        
        # 测试连接到指定数据库
        print("3. 测试连接到指定数据库...")
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )
        print("   [OK] 数据库连接成功")
        
        # 测试权限
        print("4. 测试数据库权限...")
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        print("   [OK] 基本查询权限正常")
        
        # 测试创建表权限
        try:
            cursor.execute("CREATE TABLE IF NOT EXISTS _test_permission (id INT PRIMARY KEY)")
            cursor.execute("DROP TABLE _test_permission")
            print("   [OK] 创建/删除表权限正常")
        except Exception as e:
            print(f"   [WARNING] 创建/删除表权限可能有问题: {e}")
        
        cursor.close()
        connection.close()
        
        print("=" * 50)
        print("[OK] 所有测试通过！MySQL 配置正确。")
        print("=" * 50)
        return True
        
    except pymysql.Error as e:
        print(f"[ERROR] MySQL 连接失败: {e}")
        print("\n可能的原因:")
        print("1. MySQL 服务未启动")
        print("2. 用户名或密码错误")
        print("3. 主机或端口配置错误")
        print("4. 防火墙阻止了连接")
        return False
    except Exception as e:
        print(f"[ERROR] 发生错误: {e}")
        return False

if __name__ == "__main__":
    success = test_mysql_connection()
    sys.exit(0 if success else 1)

