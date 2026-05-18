from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from sqlalchemy import ForeignKey

# 尝试加载 .env 文件（如果安装了 python-dotenv）
try:
    from dotenv import load_dotenv
    # 加载 .env 文件（如果存在）
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    # python-dotenv 未安装，跳过
    pass

# 数据库驱动：默认使用 SQLite，可通过环境变量切换到 MySQL
#   DB_DRIVER=sqlite（默认）或 mysql
DB_DRIVER = os.getenv("DB_DRIVER", "sqlite").lower()

def create_mysql_database_if_not_exists():
    """如果 MySQL 数据库不存在，则创建它"""
    try:
        import pymysql
        # 连接到 MySQL 服务器（不指定数据库）
        connection = pymysql.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            charset='utf8mb4'
        )
        cursor = connection.cursor()
        
        # 检查数据库是否存在
        db_name = os.getenv("DB_NAME", "test_openai")
        cursor.execute("SHOW DATABASES LIKE %s", (db_name,))
        result = cursor.fetchone()
        
        if not result:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"[OK] 已自动创建数据库: {db_name}")
        else:
            print(f"[OK] 数据库已存在: {db_name}")
        
        cursor.close()
        connection.close()
        return True
    except ImportError:
        print("[WARNING] pymysql 未安装，无法自动创建数据库")
        return False
    except Exception as e:
        print(f"[ERROR] 无法自动创建数据库: {e}")
        print("   请手动创建数据库或检查配置")
        return False

if DB_DRIVER == "mysql":
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "test_openai")
    
    # 尝试自动创建数据库（如果不存在）
    create_mysql_database_if_not_exists()
    
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, future=True)
else:
    # 默认使用项目根目录下的 SQLite 数据库文件
    DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "users.db"))
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        future=True,
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


# 用户模型
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)  # 角色：admin 或 user
    created_at = Column(DateTime, default=datetime.utcnow)


# API密钥模型
class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # 关联用户ID
    provider = Column(String(50), nullable=False)  # API提供商（zhipu, openai等）
    name = Column(String(100), nullable=False)  # 密钥名称（用户自定义）
    encrypted_key = Column(String(500), nullable=False)  # 加密后的API密钥
    is_default = Column(Integer, default=0)  # 是否为默认密钥（0=否，1=是）
    is_admin_key = Column(Integer, default=0)  # 是否为管理员添加的密钥（0=否，1=是），所有用户可见
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 评估体系配置模型
class EvaluationConfig(Base):
    __tablename__ = "evaluation_configs"

    id = Column(Integer, primary_key=True, index=True)
    # 基础指标权重
    base_weight = Column(String(50), default="0.8")  # 基础指标权重（80%）
    generalization_weight = Column(String(50), default="0.2")  # 通用化指标权重（20%）
    # 通用化指标内部权重
    adaptivity_weight = Column(String(50), default="0.3")  # 适应性权重（30%）
    robustness_weight = Column(String(50), default="0.3")  # 鲁棒性权重（30%）
    portability_weight = Column(String(50), default="0.2")  # 可移植性权重（20%）
    collaboration_weight = Column(String(50), default="0.2")  # 协作效率权重（20%）
    # 功能评估和安全评估权重
    func_weight = Column(String(50), default="0.7")  # 功能评估权重（70%）
    safety_weight = Column(String(50), default="0.3")  # 安全评估权重（30%）
    # 其他系数
    ground_truth_total = Column(Integer, default=None)  # 真实正例总数
    total_scene_types = Column(Integer, default=None)  # 场景类型总数
    baseline_single_task_time = Column(String(50), default=None)  # 单主体基准耗时
    baseline_adaptation_cost = Column(String(50), default=None)  # 基准适配成本
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 创建数据库表
def init_db():
    # 仅创建表（要求目标数据库已存在）
    Base.metadata.create_all(bind=engine)


# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

