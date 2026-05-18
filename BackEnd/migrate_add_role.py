"""
数据库迁移脚本：添加 role 和 is_admin_key 字段
运行此脚本以更新现有数据库表结构
"""
import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from database import engine, Base, User, ApiKey
from sqlalchemy import text

def migrate_database():
    """迁移数据库，添加新字段"""
    print("开始数据库迁移...")
    
    # 检查数据库类型
    db_url = str(engine.url)
    is_mysql = 'mysql' in db_url.lower()
    
    try:
        with engine.connect() as conn:
            # 检查 User 表是否有 role 字段
            if is_mysql:
                result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'users' 
                    AND COLUMN_NAME = 'role'
                """))
            else:
                # SQLite
                result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM pragma_table_info('users') 
                    WHERE name = 'role'
                """))
            
            has_role = result.fetchone()[0] > 0
            
            # 添加 role 字段（如果不存在）
            if not has_role:
                print("添加 role 字段到 users 表...")
                if is_mysql:
                    conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL"))
                conn.commit()
                print("[OK] role 字段已添加")
            else:
                print("[OK] role 字段已存在")
            
            # 检查 ApiKey 表是否有 is_admin_key 字段
            if is_mysql:
                result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'api_keys' 
                    AND COLUMN_NAME = 'is_admin_key'
                """))
            else:
                # SQLite
                result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM pragma_table_info('api_keys') 
                    WHERE name = 'is_admin_key'
                """))
            
            has_is_admin_key = result.fetchone()[0] > 0
            
            # 添加 is_admin_key 字段（如果不存在）
            if not has_is_admin_key:
                print("添加 is_admin_key 字段到 api_keys 表...")
                if is_mysql:
                    conn.execute(text("ALTER TABLE api_keys ADD COLUMN is_admin_key INTEGER DEFAULT 0"))
                else:
                    conn.execute(text("ALTER TABLE api_keys ADD COLUMN is_admin_key INTEGER DEFAULT 0"))
                conn.commit()
                print("[OK] is_admin_key 字段已添加")
            else:
                print("[OK] is_admin_key 字段已存在")
            
            # 更新现有用户的 role（如果为 NULL）
            if is_mysql:
                conn.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL OR role = ''"))
            else:
                conn.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL OR role = ''"))
            conn.commit()
            print("[OK] 已更新现有用户的 role 字段")
            
            # 更新现有 API key 的 is_admin_key（如果为 NULL）
            if is_mysql:
                conn.execute(text("UPDATE api_keys SET is_admin_key = 0 WHERE is_admin_key IS NULL"))
            else:
                conn.execute(text("UPDATE api_keys SET is_admin_key = 0 WHERE is_admin_key IS NULL"))
            conn.commit()
            print("[OK] 已更新现有 API key 的 is_admin_key 字段")
            
        print("\n数据库迁移完成！")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    migrate_database()

