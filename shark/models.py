from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class MembershipType(str, enum.Enum):
    NORMAL = "normal" # Default, no permission
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"
    BLACK_GOLD = "black_gold"

class MembershipLevel(Base):
    __tablename__ = "membership_levels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False) # e.g., Silver, Gold
    level_code = Column(String(20), unique=True, nullable=False) # e.g., silver, gold
    price_monthly = Column(Float, default=0.0)
    
    # Permissions / Quotas
    max_youtube_accounts = Column(Integer, default=0)
    ftp_storage_mb = Column(Integer, default=0)
    ftp_speed_kbps = Column(Integer, default=0) # in Kbps
    description = Column(String(255))

    users = relationship("User", back_populates="membership")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String(20), default=UserRole.USER) # admin or user
    membership_expire_at = Column(DateTime(timezone=True), nullable=True)
    
    # 2FA
    totp_secret = Column(String(32), nullable=True)
    is_2fa_enabled = Column(Boolean, default=False)
    
    membership_id = Column(Integer, ForeignKey("membership_levels.id"), nullable=True)
    membership = relationship("MembershipLevel", back_populates="users")
    
    youtube_accounts = relationship("YoutubeAccount", back_populates="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AccountStatus(str, enum.Enum):
    PENDING = "pending"  # 待创建
    WAIT_SECRET_UPLOADED = "wait_secret_uploaded"  # 待上传secret文件
    ACTIVE = "active"  # 生效中
    OFFLINE = "offline"  # 下线

class YoutubeAccount(Base):
    __tablename__ = "youtube_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # FTP / Account Info
    account_name = Column(String(50), unique=True, nullable=False) # This is the FTP username
    ftp_password = Column(String(100), nullable=False) # Store plain or encrypted? Usually plain needed for display or not? Requirement says "provide ftp account/password".
    
    # YouTube Auth
    client_secret_content = Column(Text, nullable=True)
    token_content = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default=AccountStatus.PENDING.value)
    machine_ip = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="youtube_accounts")
    material_configs = relationship("MaterialConfig", back_populates="youtube_account")
    schedules = relationship("UploadSchedule", back_populates="youtube_account")

class MaterialType(str, enum.Enum):
    SHORTS = "shorts"
    LONG = "long"

class MaterialConfig(Base):
    __tablename__ = "material_configs"

    id = Column(Integer, primary_key=True, index=True)
    youtube_account_id = Column(Integer, ForeignKey("youtube_accounts.id"), nullable=False)
    
    group_name = Column(String(50), nullable=False) # To identify the config group
    material_type = Column(String(20), default=MaterialType.SHORTS) # shorts or long
    video_source_dir = Column(String(255), nullable=True) # Directory path for video source
    
    # Content Templates
    title_template = Column(Text, nullable=True)
    description_template = Column(Text, nullable=True)
    tags = Column(Text, nullable=True) # Comma separated
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    youtube_account = relationship("YoutubeAccount", back_populates="material_configs")

class ScheduleType(str, enum.Enum):
    INTERVAL = "interval"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class IntervalUnit(str, enum.Enum):
    MINUTES = "minutes"
    HOURS = "hours"

class UploadSchedule(Base):
    __tablename__ = "upload_schedules"

    id = Column(Integer, primary_key=True, index=True)
    youtube_account_id = Column(Integer, ForeignKey("youtube_accounts.id"), nullable=False)
    material_config_id = Column(Integer, ForeignKey("material_configs.id"), nullable=False)
    
    # Structured Schedule Config
    schedule_type = Column(String(20), nullable=False, default=ScheduleType.INTERVAL)
    
    # For Interval
    interval_value = Column(Integer, nullable=True)
    interval_unit = Column(String(20), nullable=True) # minutes, hours
    
    # For Daily/Weekly/Monthly
    run_time = Column(String(5), nullable=True) # "HH:MM"
    
    # For Weekly
    weekdays = Column(String(50), nullable=True) # "0,1,2" (Mon,Tue,Wed)
    
    # For Monthly
    month_day = Column(Integer, nullable=True)
    
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    youtube_account = relationship("YoutubeAccount", back_populates="schedules")
    material_config = relationship("MaterialConfig")

