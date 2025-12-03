from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime
from .models import MaterialType, UserRole, ScheduleType, IntervalUnit

# Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Membership
class MembershipLevelBase(BaseModel):
    name: str
    level_code: str
    price_monthly: float
    max_youtube_accounts: int
    ftp_storage_mb: int
    ftp_speed_kbps: int
    description: Optional[str] = None

class MembershipLevelOut(MembershipLevelBase):
    id: int
    class Config:
        from_attributes = True

# User
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    role: str
    membership: Optional[MembershipLevelOut] = None
    membership_expire_at: Optional[datetime] = None
    is_2fa_enabled: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChangePassword(BaseModel):
    old_password: str
    new_password: str

class Setup2FAResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_code_base64: str

class Verify2FA(BaseModel):
    code: str

class Disable2FA(BaseModel):
    password: str

class UserUpdateAdmin(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    membership_level_code: Optional[str] = None
    membership_expire_at: Optional[datetime] = None


# Material Config
class MaterialConfigBase(BaseModel):
    group_name: str
    material_type: MaterialType
    video_source_dir: Optional[str] = None
    title_template: Optional[str] = None
    description_template: Optional[str] = None
    tags: Optional[str] = None
    is_active: bool = True

class MaterialConfigCreate(MaterialConfigBase):
    pass

class MaterialConfigOut(MaterialConfigBase):
    id: int
    youtube_account_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class PaginatedMaterialConfigOut(BaseModel):
    total: int
    items: List[MaterialConfigOut]

# Schedule
class ScheduleBase(BaseModel):
    material_config_id: int
    is_active: bool = True
    
    schedule_type: ScheduleType
    interval_value: Optional[int] = None
    interval_unit: Optional[IntervalUnit] = None
    run_time: Optional[str] = None
    weekdays: Optional[str] = None
    month_day: Optional[int] = None

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleOut(ScheduleBase):
    id: int
    youtube_account_id: int
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

class PaginatedScheduleOut(BaseModel):
    total: int
    items: List[ScheduleOut]

# Youtube Account
class YoutubeAccountBase(BaseModel):
    pass

class YoutubeAccountCreate(YoutubeAccountBase):
    # Account name is generated or provided? Requirement says "Create youtube account -> create ftp account (same name)".
    # Let's allow user to provide a desired name, or auto-generate.
    # Requirement: "create ftp account (same name youtube account)"
    desired_username: str

class YoutubeAccountOut(YoutubeAccountBase):
    id: int
    account_name: str
    ftp_password: str # Show password once or always? Requirement implies providing it.
    ftp_host: Optional[str] = None
    ftp_port: Optional[int] = None
    status: str
    machine_ip: Optional[str] = None
    created_at: datetime
    material_configs: List[MaterialConfigOut] = []
    schedules: List[ScheduleOut] = []
    
    class Config:
        from_attributes = True

class PurchaseMembership(BaseModel):
    membership_level_code: str
