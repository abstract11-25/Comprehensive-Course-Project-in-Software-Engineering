"""
数据库迁移脚本：添加 evaluation_configs 表
运行此脚本以创建评估体系配置表
"""
import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from database import engine, Base, EvaluationConfig
from sqlalchemy import text

def migrate_database():
    """迁移数据库，添加评估配置表"""
    print("开始数据库迁移...")
    
    # 检查数据库类型
    db_url = str(engine.url)
    is_mysql = 'mysql' in db_url.lower()
    
    try:
        with engine.connect() as conn:
            # 检查 evaluation_configs 表是否存在
            if is_mysql:
                result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.TABLES 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'evaluation_configs'
                """))
            else:
                # SQLite
                result = conn.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM sqlite_master 
                    WHERE type='table' AND name='evaluation_configs'
                """))
            
            table_exists = result.fetchone()[0] > 0
            
            # 如果表不存在，创建表
            if not table_exists:
                print("创建 evaluation_configs 表...")
                Base.metadata.create_all(bind=engine, tables=[EvaluationConfig.__table__])
                print("[OK] evaluation_configs 表已创建")
            else:
                print("[OK] evaluation_configs 表已存在")
            
        print("\n数据库迁移完成！")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    migrate_database()

