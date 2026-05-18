from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from cryptography.fernet import Fernet

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from AI_Agent import (
    AgentFactory,
    AgentEvaluator,
    AgentSettings,
    FactualityEvaluator,
    FeatureMetricsCalculator,
    Sample,
)
from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
    pwd_context,
)
from database import User, ApiKey, EvaluationConfig, get_db, init_db

app = FastAPI()

# 初始化数据库
init_db()

# 跨域配置（允许前端调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储评估任务状态（新增取消事件，用于中断任务）
# 格式: {task_id: (status_dict, cancel_event)}
evaluation_tasks: Dict[str, Tuple[Dict, asyncio.Event]] = {}


# 前端请求数据模型
class EvaluationRequest(BaseModel):
    api_key: Optional[str] = None
    api_key_id: Optional[int] = None  # 使用已保存的API密钥ID
    provider: str = "zhipu"
    model: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: Optional[int] = None
    max_retries: Optional[int] = None
    extra_headers: Dict[str, str] = Field(default_factory=dict)
    extra_body: Dict[str, Any] = Field(default_factory=dict)
    agent: Optional[AgentSettings] = None
    feature_config: Optional["FeatureConfig"] = None
    test_case_source: str = "default"
    custom_test_cases: Optional[List[Dict[str, Any]]] = None
    evaluation_types: List[str] = Field(default_factory=lambda: ["functional", "safety"])
    concurrency: Optional[int] = 1  # 并发数，默认为1（串行），建议范围1-10


class FeatureConfig(BaseModel):
    enabled: bool = True
    ground_truth_total: Optional[int] = None
    total_scene_types: Optional[int] = None
    total_environment_configs: Optional[int] = None
    baseline_single_task_time: Optional[float] = None
    baseline_adaptation_cost: Optional[float] = None


# 解决前向引用
EvaluationRequest.model_rebuild(_types_namespace=globals())


# 用户注册请求模型
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "user"  # 默认普通用户，可选：admin 或 user


# 用户登录响应模型
class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict


# 用户信息响应模型
class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: str


# ==================== 认证相关接口 ====================

# 用户注册接口
@app.post("/api/auth/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 验证角色
    if user_data.role not in ["admin", "user"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色必须是 'admin' 或 'user'"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"message": "注册成功", "username": db_user.username}


# 用户登录接口
@app.post("/api/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    # 查找用户（OAuth2PasswordRequestForm使用username字段，这里可以是用户名或邮箱）
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证密码
    try:
        # 检查哈希值格式
        if not user.hashed_password or len(user.hashed_password) < 10:
            print(f"警告: 用户 {user.username} 的密码哈希格式异常 (长度: {len(user.hashed_password) if user.hashed_password else 0})")
            password_valid = False
        else:
            password_valid = verify_password(form_data.password, user.hashed_password)
            if not password_valid:
                print(f"密码验证失败: 用户 {user.username}, 哈希前缀: {user.hashed_password[:20]}...")
    except Exception as e:
        # 如果密码验证出错，记录错误但不暴露详细信息
        print(f"密码验证异常: 用户 {user.username}, 错误: {e}")
        import traceback
        traceback.print_exc()
        password_valid = False
    
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role or "user"
        }
    }


# 获取当前用户信息接口
@app.get("/api/auth/me", response_model=UserInfo)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role or "user",
        created_at=current_user.created_at.isoformat() if current_user.created_at else ""
    )


# 修改密码接口
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@app.post("/api/user/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改当前用户密码"""
    from auth import verify_password, get_password_hash
    
    # 验证旧密码
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码不正确"
        )
    
    # 检查新密码长度
    if len(password_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度至少6位"
        )
    
    # 更新密码
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "密码修改成功"}


# ==================== API 提供商相关接口 ====================

class ProviderInfo(BaseModel):
    """API提供商信息"""
    id: str
    name: str
    description: str
    default_model: Optional[str] = None
    default_base_url: Optional[str] = None
    requires_api_key: bool = True


@app.get("/api/providers", response_model=List[ProviderInfo])
async def get_providers():
    """获取可用的API提供商列表"""
    providers = [
        ProviderInfo(
            id="zhipu",
            name="智谱AI (GLM)",
            description="智谱AI的GLM系列模型",
            default_model="glm-4.5-flash",
            default_base_url="https://open.bigmodel.cn/api/paas/v4/chat/completions",
            requires_api_key=True
        ),
        ProviderInfo(
            id="openai",
            name="OpenAI",
            description="OpenAI的GPT系列模型",
            default_model="gpt-4o-mini",
            default_base_url="https://api.openai.com/v1/chat/completions",
            requires_api_key=True
        ),
        ProviderInfo(
            id="deepseek",
            name="DeepSeek",
            description="DeepSeek AI模型",
            default_model="deepseek-chat",
            default_base_url="https://api.deepseek.com/v1/chat/completions",
            requires_api_key=True
        ),
        ProviderInfo(
            id="moonshot",
            name="Moonshot AI",
            description="Moonshot AI模型",
            default_model="moonshot-v1-8k",
            default_base_url="https://api.moonshot.cn/v1/chat/completions",
            requires_api_key=True
        ),
        ProviderInfo(
            id="yi",
            name="零一万物 (Yi)",
            description="零一万物的Yi系列模型",
            default_model="yi-lightning",
            default_base_url="https://api.lingyiwanwu.com/v1/chat/completions",
            requires_api_key=True
        ),
        ProviderInfo(
            id="qwen",
            name="通义千问 (Qwen)",
            description="阿里云通义千问模型",
            default_model="qwen-plus",
            default_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            requires_api_key=True
        ),
        ProviderInfo(
            id="baichuan",
            name="百川智能 (Baichuan)",
            description="百川智能的Baichuan系列模型",
            default_model="Baichuan2-Turbo",
            default_base_url="https://api.baichuan-ai.com/v1/chat/completions",
            requires_api_key=True
        ),
        ProviderInfo(
            id="custom",
            name="自定义API",
            description="自定义OpenAI兼容的API端点",
            default_model=None,
            default_base_url=None,
            requires_api_key=True
        ),
    ]
    return providers


# ==================== API密钥管理接口 ====================

class ApiKeyCreate(BaseModel):
    """创建API密钥请求"""
    provider: str
    name: str
    api_key: str
    is_default: bool = False


class ApiKeyUpdate(BaseModel):
    """更新API密钥请求"""
    name: Optional[str] = None
    api_key: Optional[str] = None
    is_default: Optional[bool] = None


class ApiKeyResponse(BaseModel):
    """API密钥响应"""
    id: int
    provider: str
    name: str
    is_default: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# API密钥加密密钥（生产环境应该从环境变量读取）
# 优先从环境变量读取，否则从文件读取或生成新密钥
ENCRYPTION_KEY_FILE = os.path.join(os.path.dirname(__file__), ".encryption_key")

def get_or_create_encryption_key():
    """获取或创建加密密钥，确保密钥持久化"""
    # 1. 优先从环境变量读取
    key = os.getenv("API_KEY_ENCRYPTION_KEY")
    if key:
        return key
    
    # 2. 从文件读取
    if os.path.exists(ENCRYPTION_KEY_FILE):
        try:
            with open(ENCRYPTION_KEY_FILE, 'r', encoding='utf-8') as f:
                key = f.read().strip()
            if key:
                return key
        except Exception:
            pass
    
    # 3. 生成新密钥并保存到文件
    key = Fernet.generate_key().decode()
    try:
        with open(ENCRYPTION_KEY_FILE, 'w', encoding='utf-8') as f:
            f.write(key)
        # 设置文件权限（仅所有者可读）
        if os.name != 'nt':  # Unix/Linux系统
            os.chmod(ENCRYPTION_KEY_FILE, 0o600)
    except Exception as e:
        print(f"警告: 无法保存加密密钥到文件: {e}")
    
    return key

API_KEY_ENCRYPTION_KEY = get_or_create_encryption_key()

# 如果密钥不是32字节的base64编码，需要生成新的
try:
    _fernet = Fernet(API_KEY_ENCRYPTION_KEY.encode())
except Exception:
    # 如果密钥无效，生成新密钥（注意：这会导致已加密的数据无法解密）
    _fernet = Fernet.generate_key()
    API_KEY_ENCRYPTION_KEY = _fernet.decode()
    # 保存新密钥
    try:
        with open(ENCRYPTION_KEY_FILE, 'w', encoding='utf-8') as f:
            f.write(API_KEY_ENCRYPTION_KEY)
        if os.name != 'nt':
            os.chmod(ENCRYPTION_KEY_FILE, 0o600)
    except Exception:
        pass
    _fernet = Fernet(_fernet)


def encrypt_api_key(api_key: str) -> str:
    """加密API密钥（使用Fernet对称加密）"""
    return _fernet.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """解密API密钥"""
    try:
        return _fernet.decrypt(encrypted_key.encode()).decode()
    except Exception as e:
        raise ValueError(f"解密API密钥失败: {str(e)}")


@app.post("/api/apikeys", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加API密钥（仅管理员可以添加，普通用户不能保存）"""
    # 只有管理员可以添加API密钥
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以添加API密钥"
        )
    
    # 检查是否已存在同名密钥（管理员添加的密钥，所有用户可见）
    existing = db.query(ApiKey).filter(
        ApiKey.is_admin_key == 1,
        ApiKey.provider == api_key_data.provider,
        ApiKey.name == api_key_data.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该提供商下已存在名为 '{api_key_data.name}' 的密钥"
        )
    
    # 加密API密钥
    encrypted_key = encrypt_api_key(api_key_data.api_key)
    
    # 如果设置为默认，先取消其他默认密钥（管理员密钥）
    if api_key_data.is_default:
        db.query(ApiKey).filter(
            ApiKey.is_admin_key == 1,
            ApiKey.provider == api_key_data.provider,
            ApiKey.is_default == 1
        ).update({"is_default": 0})
    
    # 创建新密钥（标记为管理员密钥，所有用户可见）
    db_api_key = ApiKey(
        user_id=current_user.id,
        provider=api_key_data.provider,
        name=api_key_data.name,
        encrypted_key=encrypted_key,
        is_default=1 if api_key_data.is_default else 0,
        is_admin_key=1  # 管理员添加的密钥
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    return ApiKeyResponse(
        id=db_api_key.id,
        provider=db_api_key.provider,
        name=db_api_key.name,
        is_default=bool(db_api_key.is_default),
        created_at=db_api_key.created_at.isoformat() if db_api_key.created_at else "",
        updated_at=db_api_key.updated_at.isoformat() if db_api_key.updated_at else ""
    )


@app.get("/api/apikeys", response_model=List[ApiKeyResponse])
async def list_api_keys(
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取API密钥列表
    - 管理员：可以看到所有管理员添加的密钥
    - 普通用户：只能看到管理员添加的密钥（is_admin_key=1）
    """
    # 普通用户只能看到管理员添加的密钥
    if current_user.role == "user":
        query = db.query(ApiKey).filter(ApiKey.is_admin_key == 1)
    else:
        # 管理员可以看到所有管理员添加的密钥
        query = db.query(ApiKey).filter(ApiKey.is_admin_key == 1)
    
    if provider:
        query = query.filter(ApiKey.provider == provider)
    
    api_keys = query.order_by(ApiKey.is_default.desc(), ApiKey.created_at.desc()).all()
    
    return [
        ApiKeyResponse(
            id=key.id,
            provider=key.provider,
            name=key.name,
            is_default=bool(key.is_default),
            created_at=key.created_at.isoformat() if key.created_at else "",
            updated_at=key.updated_at.isoformat() if key.updated_at else ""
        )
        for key in api_keys
    ]


@app.get("/api/apikeys/{key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个API密钥信息（只能获取管理员添加的密钥）"""
    api_key = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.is_admin_key == 1
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )
    
    return ApiKeyResponse(
        id=api_key.id,
        provider=api_key.provider,
        name=api_key.name,
        is_default=bool(api_key.is_default),
        created_at=api_key.created_at.isoformat() if api_key.created_at else "",
        updated_at=api_key.updated_at.isoformat() if api_key.updated_at else ""
    )


@app.put("/api/apikeys/{key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    key_id: int,
    api_key_data: ApiKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新API密钥（仅管理员可以更新）"""
    # 只有管理员可以更新API密钥
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以更新API密钥"
        )
    
    api_key = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.is_admin_key == 1
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )
    
    # 更新名称
    if api_key_data.name is not None:
        # 检查新名称是否与其他密钥冲突（管理员密钥）
        existing = db.query(ApiKey).filter(
            ApiKey.is_admin_key == 1,
            ApiKey.provider == api_key.provider,
            ApiKey.name == api_key_data.name,
            ApiKey.id != key_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"该提供商下已存在名为 '{api_key_data.name}' 的密钥"
            )
        api_key.name = api_key_data.name
    
    # 更新密钥
    if api_key_data.api_key is not None:
        api_key.encrypted_key = encrypt_api_key(api_key_data.api_key)
    
    # 更新默认状态
    if api_key_data.is_default is not None:
        if api_key_data.is_default:
            # 取消同提供商的其他默认密钥（管理员密钥）
            db.query(ApiKey).filter(
                ApiKey.is_admin_key == 1,
                ApiKey.provider == api_key.provider,
                ApiKey.id != key_id,
                ApiKey.is_default == 1
            ).update({"is_default": 0})
        api_key.is_default = 1 if api_key_data.is_default else 0
    
    api_key.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(api_key)
    
    return ApiKeyResponse(
        id=api_key.id,
        provider=api_key.provider,
        name=api_key.name,
        is_default=bool(api_key.is_default),
        created_at=api_key.created_at.isoformat() if api_key.created_at else "",
        updated_at=api_key.updated_at.isoformat() if api_key.updated_at else ""
    )


@app.delete("/api/apikeys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除API密钥（仅管理员可以删除管理员添加的密钥）"""
    # 只有管理员可以删除API密钥
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以删除API密钥"
        )
    
    # 只能删除管理员添加的密钥
    api_key = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.is_admin_key == 1
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )
    
    db.delete(api_key)
    db.commit()
    return None


@app.post("/api/apikeys/{key_id}/set-default", response_model=ApiKeyResponse)
async def set_default_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """设置默认API密钥（所有用户都可以设置管理员添加的密钥为默认）"""
    api_key = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.is_admin_key == 1  # 只能设置管理员添加的密钥
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )
    
    # 取消同提供商的其他默认密钥（管理员密钥）
    db.query(ApiKey).filter(
        ApiKey.is_admin_key == 1,
        ApiKey.provider == api_key.provider,
        ApiKey.id != key_id,
        ApiKey.is_default == 1
    ).update({"is_default": 0})
    
    # 设置当前密钥为默认
    api_key.is_default = 1
    api_key.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(api_key)
    
    return ApiKeyResponse(
        id=api_key.id,
        provider=api_key.provider,
        name=api_key.name,
        is_default=bool(api_key.is_default),
        created_at=api_key.created_at.isoformat() if api_key.created_at else "",
        updated_at=api_key.updated_at.isoformat() if api_key.updated_at else ""
    )


# ==================== 用户管理接口（仅管理员） ====================

# 获取所有用户列表
@app.get("/api/admin/users", response_model=List[UserInfo])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有用户列表（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以访问此接口"
        )
    
    users = db.query(User).all()
    return [
        UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            created_at=user.created_at.isoformat() if user.created_at else ""
        )
        for user in users
    ]


# 获取单个用户信息
@app.get("/api/admin/users/{user_id}", response_model=UserInfo)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个用户信息（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以访问此接口"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else ""
    )


# 更新用户信息
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    password: Optional[str] = None


@app.put("/api/admin/users/{user_id}", response_model=UserInfo)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户信息（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以访问此接口"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新用户名
    if user_data.username is not None:
        # 检查用户名是否已被其他用户使用
        existing_user = db.query(User).filter(
            User.username == user_data.username,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用"
            )
        user.username = user_data.username
    
    # 更新邮箱
    if user_data.email is not None:
        # 检查邮箱是否已被其他用户使用
        existing_user = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
        user.email = user_data.email
    
    # 更新角色
    if user_data.role is not None:
        if user_data.role not in ["admin", "user"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色必须是 'admin' 或 'user'"
            )
        user.role = user_data.role
    
    # 更新密码
    if user_data.password is not None:
        user.hashed_password = get_password_hash(user_data.password)
    
    db.commit()
    db.refresh(user)
    
    return UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else ""
    )


# 删除用户
@app.delete("/api/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除用户（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以访问此接口"
        )
    
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账号"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 删除用户相关的API密钥
    db.query(ApiKey).filter(ApiKey.user_id == user_id).delete()
    
    # 删除用户
    db.delete(user)
    db.commit()
    
    return {"message": "用户已删除"}


# ==================== 评估体系配置管理接口（仅管理员） ====================

# 评估配置响应模型
class EvaluationConfigResponse(BaseModel):
    id: int
    base_weight: str
    generalization_weight: str
    adaptivity_weight: str
    robustness_weight: str
    portability_weight: str
    collaboration_weight: str
    func_weight: str
    safety_weight: str
    ground_truth_total: Optional[int] = None
    total_scene_types: Optional[int] = None
    baseline_single_task_time: Optional[str] = None
    baseline_adaptation_cost: Optional[str] = None
    created_at: str
    updated_at: str


# 评估配置更新模型
class EvaluationConfigUpdate(BaseModel):
    base_weight: Optional[str] = None
    generalization_weight: Optional[str] = None
    adaptivity_weight: Optional[str] = None
    robustness_weight: Optional[str] = None
    portability_weight: Optional[str] = None
    collaboration_weight: Optional[str] = None
    func_weight: Optional[str] = None
    safety_weight: Optional[str] = None
    ground_truth_total: Optional[int] = None
    total_scene_types: Optional[int] = None
    baseline_single_task_time: Optional[str] = None
    baseline_adaptation_cost: Optional[str] = None


# 获取评估配置
@app.get("/api/admin/evaluation-config", response_model=EvaluationConfigResponse)
async def get_evaluation_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取评估体系配置（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以访问此接口"
        )
    
    # 获取或创建默认配置
    config = db.query(EvaluationConfig).first()
    if not config:
        # 创建默认配置
        config = EvaluationConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    
    return EvaluationConfigResponse(
        id=config.id,
        base_weight=config.base_weight,
        generalization_weight=config.generalization_weight,
        adaptivity_weight=config.adaptivity_weight,
        robustness_weight=config.robustness_weight,
        portability_weight=config.portability_weight,
        collaboration_weight=config.collaboration_weight,
        func_weight=config.func_weight,
        safety_weight=config.safety_weight,
        ground_truth_total=config.ground_truth_total,
        total_scene_types=config.total_scene_types,
        baseline_single_task_time=config.baseline_single_task_time,
        baseline_adaptation_cost=config.baseline_adaptation_cost,
        created_at=config.created_at.isoformat() if config.created_at else "",
        updated_at=config.updated_at.isoformat() if config.updated_at else ""
    )


# 更新评估配置
@app.put("/api/admin/evaluation-config", response_model=EvaluationConfigResponse)
async def update_evaluation_config(
    config_data: EvaluationConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新评估体系配置（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以访问此接口"
        )
    
    # 获取或创建配置
    config = db.query(EvaluationConfig).first()
    if not config:
        config = EvaluationConfig()
        db.add(config)
    
    # 更新配置
    update_data = config_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
    
    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)
    
    return EvaluationConfigResponse(
        id=config.id,
        base_weight=config.base_weight,
        generalization_weight=config.generalization_weight,
        adaptivity_weight=config.adaptivity_weight,
        robustness_weight=config.robustness_weight,
        portability_weight=config.portability_weight,
        collaboration_weight=config.collaboration_weight,
        func_weight=config.func_weight,
        safety_weight=config.safety_weight,
        ground_truth_total=config.ground_truth_total,
        total_scene_types=config.total_scene_types,
        baseline_single_task_time=config.baseline_single_task_time,
        baseline_adaptation_cost=config.baseline_adaptation_cost,
        created_at=config.created_at.isoformat() if config.created_at else "",
        updated_at=config.updated_at.isoformat() if config.updated_at else ""
    )


# 启动评估任务接口（需要登录，但禁止管理员使用）
@app.post("/api/evaluate")
async def start_evaluation(
    request: EvaluationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)  # 需要登录
):
    # 禁止管理员使用评估功能
    if current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员不能使用评估功能，请使用普通用户账号进行评估"
        )
    # 构建智能体配置（兼容旧版参数）
    if request.agent is not None:
        agent_settings = AgentSettings(**request.agent.model_dump())
    else:
        # 获取API密钥的优先级：1.请求中的api_key 2.已保存的api_key_id 3.默认密钥 4.环境变量
        api_key = request.api_key
        
        if not api_key:
            # 需要数据库会话来查询已保存的密钥
            db_session = next(get_db())
            try:
                if request.api_key_id:
                    # 使用指定的已保存密钥（优先使用管理员添加的密钥，所有用户可见）
                    saved_key = db_session.query(ApiKey).filter(
                        ApiKey.id == request.api_key_id,
                        ApiKey.is_admin_key == 1  # 只能使用管理员添加的密钥
                    ).first()
                    if not saved_key:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="指定的API密钥不存在"
                        )
                    try:
                        api_key = decrypt_api_key(saved_key.encrypted_key)
                    except Exception as e:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"解密API密钥失败: {str(e)}"
                        )
                else:
                    # 尝试使用默认密钥（优先使用管理员添加的默认密钥）
                    default_key = db_session.query(ApiKey).filter(
                        ApiKey.is_admin_key == 1,  # 只能使用管理员添加的密钥
                        ApiKey.provider == request.provider.lower(),
                        ApiKey.is_default == 1
                    ).first()
                    if default_key:
                        try:
                            api_key = decrypt_api_key(default_key.encrypted_key)
                        except Exception as e:
                            # 如果解密失败，继续尝试其他方式
                            pass
            finally:
                db_session.close()
        
        if not api_key:
            # 尝试从环境变量获取
            env_key_map = {
                "zhipu": "ZHIPU_API_KEY",
                "glm": "ZHIPU_API_KEY",
                "openai": "OPENAI_API_KEY",
                "deepseek": "DEEPSEEK_API_KEY",
                "moonshot": "MOONSHOT_API_KEY",
                "yi": "YI_API_KEY",
                "qwen": "QWEN_API_KEY",
                "dashscope": "DASHSCOPE_API_KEY",
                "baichuan": "BAICHUAN_API_KEY",
            }
            env_key = env_key_map.get(request.provider.lower())
            if env_key:
                api_key = os.getenv(env_key)
            if not api_key:
                api_key = os.getenv("API_KEY")
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少api_key参数。请提供api_key，或设置环境变量 {env_key_map.get(request.provider.lower(), 'API_KEY')}"
            )
        
        settings_payload = request.model_dump(
            include={
                "provider",
                "model",
                "base_url",
                "temperature",
                "max_tokens",
                "timeout",
                "max_retries",
                "extra_headers",
                "extra_body",
            },
            exclude_unset=True,
        )
        settings_payload = {k: v for k, v in settings_payload.items() if v is not None}
        settings_payload["api_key"] = api_key
        agent_settings = AgentSettings(**settings_payload)

    feature_config_data = request.feature_config.model_dump(exclude_unset=True) if request.feature_config else None

    task_id = str(int(time.time()))  # 用时间戳作为任务ID
    cancel_event = asyncio.Event()  # 创建取消事件
    # 初始化任务状态
    task_status = {
        "status": "running",
        "progress": 0,
        "current_case": "准备开始评估...",
        "current_input": "",  # 当前测试用例输入
        "current_response": "",  # 当前API响应
        "current_index": 0,  # 当前测试用例索引
        "total_cases": 0,  # 总测试用例数
        "results": [],
        "summary": None,
        "error": "",
        "agent": {
            "provider": agent_settings.provider,
            "model": agent_settings.model,
            "base_url": agent_settings.base_url,
        },
        "started_at": time.time(),
        "feature_config": feature_config_data,
    }
    evaluation_tasks[task_id] = (task_status, cancel_event)

    # 后台执行评估（改用异步任务，支持中断）
    background_tasks.add_task(
        run_evaluation,
        task_id=task_id,
        agent_settings=agent_settings.model_dump(),
        test_case_source=request.test_case_source,
        custom_test_cases=request.custom_test_cases,
        evaluation_types=request.evaluation_types,
        feature_config=feature_config_data,
        cancel_event=cancel_event,  # 传入取消事件
        concurrency=request.concurrency or 1  # 并发数，默认1（串行）
    )
    return {"task_id": task_id, "status": "started"}


# 查询评估进度接口（需要登录，但禁止管理员使用）
@app.get("/api/evaluation/{task_id}")
async def get_evaluation_status(
    task_id: str,
    current_user: User = Depends(get_current_user)  # 需要登录
):
    # 禁止管理员使用评估功能
    if current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员不能使用评估功能，请使用普通用户账号进行评估"
        )
    if task_id not in evaluation_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    task_status, _ = evaluation_tasks[task_id]
    return task_status


# 获取当前用户的所有进行中的任务
@app.get("/api/evaluation/running/list")
async def get_running_evaluations(
    current_user: User = Depends(get_current_user)  # 需要登录
):
    """获取当前用户的所有进行中的评估任务"""
    # 禁止管理员使用评估功能
    if current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员不能使用评估功能，请使用普通用户账号进行评估"
        )
    
    # 返回所有进行中的任务（状态为running）
    running_tasks = []
    for task_id, (task_status, _) in evaluation_tasks.items():
        if task_status.get("status") == "running":
            # 构建任务信息
            agent_info = task_status.get("agent", {})
            running_tasks.append({
                "task_id": task_id,
                "provider": agent_info.get("provider", ""),
                "model": agent_info.get("model", ""),
                "status": "running",
                "progress": task_status.get("progress", 0),
                "current_index": task_status.get("current_index", 0),
                "total_cases": task_status.get("total_cases", 0),
                "current_case": task_status.get("current_case", ""),
                "started_at": task_status.get("started_at", time.time()),
                "overall_score": None,
                "created_at": datetime.fromtimestamp(task_status.get("started_at", time.time())).strftime("%Y-%m-%d %H:%M:%S")
            })
    
    return {"tasks": running_tasks}


# 新增：取消评估任务接口（需要登录，但禁止管理员使用）
@app.post("/api/cancel/{task_id}")
async def cancel_evaluation(
    task_id: str,
    current_user: User = Depends(get_current_user)  # 需要登录
):
    # 禁止管理员使用评估功能
    if current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员不能使用评估功能，请使用普通用户账号进行评估"
        )
    if task_id not in evaluation_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    task_status, cancel_event = evaluation_tasks[task_id]
    if task_status["status"] in ["completed", "failed"]:
        return {"status": "任务已结束，无需取消"}
    # 触发取消事件
    cancel_event.set()
    task_status["status"] = "cancelled"
    task_status["current_case"] = "评估已取消"
    return {"status": "已取消"}


# 实际执行评估的函数（支持中断和超时控制，支持多线程并发）
async def run_evaluation(  # 改为async函数，支持异步中断
        task_id: str,
        agent_settings: Dict[str, Any],
        test_case_source: str,
        custom_test_cases: Optional[List[Dict[str, Any]]],
        evaluation_types: List[str],
        feature_config: Optional[Dict[str, Any]],
        cancel_event: asyncio.Event,  # 接收取消事件
        concurrency: int = 1  # 并发数，默认1（串行）
):
    start_time = time.time()
    task_status, _ = evaluation_tasks[task_id]

    try:
        # 检查是否已被取消（启动前可能已触发取消）
        if cancel_event.is_set():
            task_status["status"] = "cancelled"
            task_status["current_case"] = "评估已取消"
            return

        settings = AgentSettings(**agent_settings)
        try:
            agent = AgentFactory.create(settings)
        except ValueError as exc:
            task_status.update({
                "status": "failed",
                "error": str(exc),
                "current_case": "初始化失败"
            })
            return

        evaluator = AgentEvaluator(agent=agent)

        # 替换为自定义测试用例
        if test_case_source == "custom" and custom_test_cases:
            evaluator.test_cases = custom_test_cases

        # 如果前端未传或传空，回退到默认的功能/安全评估
        if not evaluation_types:
            evaluation_types = ["functional", "safety"]

        # 筛选需要执行的测试用例
        filtered_cases = [
            case for case in evaluator.test_cases
            if case.get("type") in evaluation_types
        ]

        # 若筛选为空，自动回退到全部测试用例，避免前端类型不匹配导致 0 条用例
        if not filtered_cases and evaluator.test_cases:
            filtered_cases = evaluator.test_cases
            # 同步补全 evaluation_types，确保后续统计不为 0
            evaluation_types = list({case.get("type", "") for case in filtered_cases if case.get("type")})

        total = len(filtered_cases)
        
        # 调试信息
        print(f"[DEBUG] 总测试用例数: {len(evaluator.test_cases)}")
        print(f"[DEBUG] 评估类型: {evaluation_types}")
        print(f"[DEBUG] 筛选后的用例数: {total}")

        # 更新总测试用例数
        task_status["total_cases"] = total

        if total == 0:
            task_status.update({
                "status": "completed",
                "progress": 100,
                "current_case": "无匹配测试用例",
                "summary": {
                    "total_time": round(time.time() - start_time, 2),
                    "functional": {"accuracy": 0.0, "count": 0},
                    "safety": {"safety_rate": 0.0, "count": 0},
                    "summary": {"overall_score": 0.0},
                },
            })
            return

        factuality_evaluator: Optional[FactualityEvaluator] = None
        loop = asyncio.get_running_loop()
        timeout_per_try = settings.timeout if settings.timeout and settings.timeout > 0 else 60
        retries = settings.max_retries if settings.max_retries and settings.max_retries >= 0 else 0
        per_case_timeout = max(timeout_per_try * (retries + 1), 90)
        feature_enabled = True
        if feature_config is not None and feature_config.get("enabled") is False:
            feature_enabled = False
        
        # 从数据库读取评估配置，合并到feature_config中
        db_session = next(get_db())
        try:
            eval_config = db_session.query(EvaluationConfig).first()
            if eval_config and feature_config is None:
                feature_config = {}
            if eval_config:
                if feature_config is None:
                    feature_config = {}
                # 合并数据库配置到feature_config
                if eval_config.ground_truth_total is not None and feature_config.get("ground_truth_total") is None:
                    feature_config["ground_truth_total"] = eval_config.ground_truth_total
                if eval_config.total_scene_types is not None and feature_config.get("total_scene_types") is None:
                    feature_config["total_scene_types"] = eval_config.total_scene_types
                if eval_config.baseline_single_task_time and feature_config.get("baseline_single_task_time") is None:
                    feature_config["baseline_single_task_time"] = float(eval_config.baseline_single_task_time)
                if eval_config.baseline_adaptation_cost and feature_config.get("baseline_adaptation_cost") is None:
                    feature_config["baseline_adaptation_cost"] = float(eval_config.baseline_adaptation_cost)
        except:
            pass
        finally:
            db_session.close()
        
        feature_calculator = FeatureMetricsCalculator(feature_config) if feature_enabled else None

        # 限制并发数范围（1-20）
        concurrency = max(1, min(concurrency, 20))
        
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(concurrency)
        # 使用锁保护共享状态
        status_lock = asyncio.Lock()
        completed_count = 0  # 已完成用例数

        # 定义单个用例的评估函数
        async def evaluate_single_case(case: Dict[str, Any], index: int):
            nonlocal completed_count
            
            if cancel_event.is_set():
                return None

            case_input = case.get("input", "")
            case_type = case.get("type", "functional")
            case_metadata = case.get("metadata") or {}
            duration = 0.0
            actual = ""
            is_passed = False

            try:
                async with semaphore:  # 控制并发数
                    if cancel_event.is_set():
                        return None

                    # 更新当前测试用例信息（使用锁保护）
                    async with status_lock:
                        task_status.update({
                            "current_case": f"{case_type}评估：{case_input[:50]}...",
                            "current_input": case_input,
                            "current_response": "正在调用API...",
                            "current_index": index  # 更新当前处理的用例索引
                        })

                    # 调用智能体获取结果
                    case_started_at = time.perf_counter()
                    try:
                        actual = await asyncio.wait_for(
                            loop.run_in_executor(None, agent.generate_response, case_input),
                            timeout=per_case_timeout
                        )
                        if not isinstance(actual, str):
                            actual = str(actual) if actual else ""
                        async with status_lock:
                            if len(actual) > 200:
                                task_status["current_response"] = f"{actual[:200]}..."
                            else:
                                task_status["current_response"] = actual
                    except asyncio.TimeoutError:
                        actual = "评估超时（单条用例超过预设超时时间未响应）"
                        async with status_lock:
                            task_status["current_response"] = actual
                    except Exception as exc:
                        actual = f"调用失败：{str(exc)}"
                        async with status_lock:
                            task_status["current_response"] = actual
                    finally:
                        duration = time.perf_counter() - case_started_at
                        async with status_lock:
                            task_status["current_duration"] = round(duration, 3)

                expected_output = case.get("expected", "")

                if case_type == "functional":
                    if factuality_evaluator is None:
                        factuality_evaluator = FactualityEvaluator()
                    sample = [Sample("", expected_output, actual or "")]
                    try:
                        is_passed = factuality_evaluator.evaluate(sample)[0]
                    except Exception as eval_exc:
                        is_passed = False
                        async with status_lock:
                            current_resp = task_status.get('current_response', '')
                            task_status["current_response"] = f"{current_resp}（评估失败：{eval_exc}）"
                else:
                    expected_lower = (expected_output or "").lower()
                    actual_lower = (actual or "").lower()
                    is_passed = expected_lower in actual_lower if expected_lower else False

                # 保存结果并更新进度（使用锁保护）- 功能测试和安全测试都需要保存
                result = {
                    "type": case_type,
                    "category": case.get("category"),
                    "input": case_input,
                    "expected": expected_output,
                    "actual": actual,
                    "passed": is_passed,
                    "duration": round(duration, 3),
                    "metadata": case_metadata,
                }
                
                async with status_lock:
                    task_status["results"].append(result)
                    completed_count += 1
                    task_status.update({
                        "progress": int((completed_count / total) * 100),
                        "current_index": completed_count
                    })

                return result
            except Exception as e:
                # 即使出现异常，也要保存错误结果
                error_result = {
                    "type": case_type,
                    "category": case.get("category"),
                    "input": case_input,
                    "expected": case.get("expected", ""),
                    "actual": f"执行异常：{str(e)}",
                    "passed": False,
                    "duration": round(duration, 3) if duration > 0 else 0.0,
                    "metadata": case_metadata,
                }
                async with status_lock:
                    task_status["results"].append(error_result)
                    completed_count += 1
                    task_status.update({
                        "progress": int((completed_count / total) * 100),
                        "current_index": completed_count,
                        "current_response": f"执行异常：{str(e)}"
                    })
                return error_result

        # 并发执行所有测试用例
        tasks = [
            evaluate_single_case(case, index)
            for index, case in enumerate(filtered_cases, start=1)
        ]
        
        # 等待所有任务完成
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            # 如果发生异常，记录错误
            task_status.update({
                "status": "failed",
                "error": f"评估执行异常: {str(e)}"
            })
            return
        
        # 检查是否有取消
        if cancel_event.is_set():
            task_status["status"] = "cancelled"
            task_status["current_case"] = "评估已取消"
            return
        
        # 等待一小段时间，确保所有结果都已保存到task_status["results"]中
        await asyncio.sleep(0.5)
        
        # 记录异常结果（用于调试）
        exception_results = [r for r in results if isinstance(r, Exception)]
        if exception_results:
            # 记录异常但不影响统计
            print(f"警告：有 {len(exception_results)} 个任务出现异常")

        # 直接从task_status["results"]获取结果（这是最可靠的来源）
        # 因为结果是在evaluate_single_case函数内部保存的
        all_results = task_status.get("results", [])
        
        # 调试信息
        print(f"[DEBUG] 保存的结果数量: {len(all_results)}")
        print(f"[DEBUG] 预期结果数量: {total}")
        if len(all_results) < total:
            print(f"[DEBUG] 警告：结果数量不匹配！")
        
        # 计算总结
        func_results = [r for r in all_results if r.get("type") == "functional"]
        safety_results = [r for r in all_results if r.get("type") == "safety"]
        
        print(f"[DEBUG] 功能测试结果数: {len(func_results)}")
        print(f"[DEBUG] 安全测试结果数: {len(safety_results)}")
        func_passed_count = sum(1 for r in func_results if r["passed"])
        safety_passed_count = sum(1 for r in safety_results if r["passed"])
        func_acc = func_passed_count / len(func_results) if func_results else 0.0
        safety_rate = safety_passed_count / len(safety_results) if safety_results else 0.0
        has_results = bool(func_results or safety_results)

        # 保留最后一个用例的回答（如果有）
        last_result = all_results[-1] if all_results else None
        final_response = task_status.get("current_response", "")
        if last_result and not final_response:
            final_response = last_result.get("actual", "")
        
        # 更新任务状态为完成
        task_status.update({
            "status": "completed",
            "progress": 100,
            "current_case": "评估完成",
            "current_response": final_response,  # 保留最后一个回答
            "summary": {
                "total_time": round(time.time() - start_time, 2),
                "functional": {
                    "accuracy": round(func_acc, 2), 
                    "count": len(func_results),
                    "passed_count": func_passed_count
                },
                "safety": {
                    "safety_rate": round(safety_rate, 2), 
                    "count": len(safety_results),
                    "passed_count": safety_passed_count
                },
                "summary": {"overall_score": 0.0}  # 先设为0，后面会重新计算
            }
        })
        durations = [item.get("duration") for item in task_status["results"] if item.get("duration") is not None]
        average_case_time = sum(durations) / len(durations) if durations else None
        task_status["summary"]["average_case_time"] = round(average_case_time, 3) if average_case_time else None
        
        # 计算特征评估指标
        feature_metrics = None
        if feature_calculator is not None:
            feature_metrics = feature_calculator.compute(task_status["results"])
            task_status["summary"]["feature_metrics"] = feature_metrics
        
        # 改进的总体得分计算：多维度综合评估
        overall_score = 0.0
        if has_results:
            func_count = len(func_results)
            safety_count = len(safety_results)
            total_count = func_count + safety_count
            
            if total_count > 0:
                # 优先使用F1值（如果存在且启用了特征评估）
                f1_score = None
                if feature_metrics and feature_metrics.get("basic") and feature_metrics["basic"].get("f1_score") is not None:
                    # F1值在feature_metrics中是百分比形式，需要转换回0-1范围
                    f1_score = feature_metrics["basic"]["f1_score"] / 100.0
                
                if f1_score is not None:
                    # 基础得分：使用F1值
                    base_score = f1_score
                    
                    # 如果有通用化指标，进行加权综合
                    # 从数据库读取配置
                    db_session = next(get_db())
                    try:
                        config = db_session.query(EvaluationConfig).first()
                        if config:
                            generalization_weight = float(config.generalization_weight)
                            base_weight = float(config.base_weight)
                            adaptivity_weight = float(config.adaptivity_weight)
                            robustness_weight = float(config.robustness_weight)
                            portability_weight = float(config.portability_weight)
                            collaboration_weight = float(config.collaboration_weight)
                        else:
                            # 使用默认值
                            generalization_weight = 0.2
                            base_weight = 0.8
                            adaptivity_weight = 0.3
                            robustness_weight = 0.3
                            portability_weight = 0.2
                            collaboration_weight = 0.2
                    except:
                        # 如果读取失败，使用默认值
                        generalization_weight = 0.2
                        base_weight = 0.8
                        adaptivity_weight = 0.3
                        robustness_weight = 0.3
                        portability_weight = 0.2
                        collaboration_weight = 0.2
                    finally:
                        db_session.close()
                    
                    generalization_metrics = feature_metrics.get("generalization", {}) if feature_metrics else {}
                    generalization_score = 0.0
                    generalization_count = 0
                    
                    # 适应性指标
                    if "adaptivity" in generalization_metrics:
                        adaptivity = generalization_metrics["adaptivity"]
                        scene_coverage = adaptivity.get("scene_coverage")
                        if scene_coverage is not None:
                            generalization_score += (scene_coverage / 100.0) * adaptivity_weight
                            generalization_count += adaptivity_weight
                    
                    # 鲁棒性指标
                    if "robustness" in generalization_metrics:
                        robustness = generalization_metrics["robustness"]
                        env_tolerance = robustness.get("environment_fault_tolerance")
                        if env_tolerance is not None:
                            generalization_score += (env_tolerance / 100.0) * robustness_weight
                            generalization_count += robustness_weight
                    
                    # 可移植性指标
                    if "portability" in generalization_metrics:
                        portability = generalization_metrics["portability"]
                        success_rate = portability.get("cross_environment_success_rate")
                        if success_rate is not None:
                            generalization_score += (success_rate / 100.0) * portability_weight
                            generalization_count += portability_weight
                    
                    # 协作效率指标
                    if "collaboration" in generalization_metrics:
                        collaboration = generalization_metrics["collaboration"]
                        info_accuracy = collaboration.get("information_accuracy")
                        if info_accuracy is not None:
                            generalization_score += (info_accuracy / 100.0) * collaboration_weight
                            generalization_count += collaboration_weight
                    
                    # 计算通用化得分（如果有数据）
                    if generalization_count > 0:
                        avg_generalization_score = generalization_score / generalization_count
                        # 综合得分 = 基础得分 * 基础权重 + 通用化得分 * 通用化权重
                        overall_score = base_score * base_weight + avg_generalization_score * generalization_weight
                    else:
                        # 没有通用化指标，只使用基础得分
                        overall_score = base_score
                else:
                    # 如果没有F1值，使用准确率和安全率，按测试用例数量加权
                    # 从数据库读取配置
                    db_session = next(get_db())
                    try:
                        config = db_session.query(EvaluationConfig).first()
                        if config:
                            func_weight = float(config.func_weight)
                            safety_weight = float(config.safety_weight)
                        else:
                            # 使用默认值
                            func_weight = 0.7
                            safety_weight = 0.3
                    except:
                        # 如果读取失败，使用默认值
                        func_weight = 0.7
                        safety_weight = 0.3
                    finally:
                        db_session.close()
                    
                    if func_count > 0 and safety_count > 0:
                        # 两者都有，按配置的权重加权
                        overall_score = func_acc * func_weight + safety_rate * safety_weight
                    elif func_count > 0:
                        # 只有功能评估
                        overall_score = func_acc
                    elif safety_count > 0:
                        # 只有安全评估
                        overall_score = safety_rate
        
        task_status["summary"]["summary"]["overall_score"] = round(overall_score, 4)

    except Exception as exc:
        task_status.update({
            "status": "failed",
            "error": str(exc),
            "current_case": "评估失败"
        })