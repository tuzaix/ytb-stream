from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class TitleDesc(BaseModel):
    title: str
    description: str

class Account(BaseModel):
    name: str  # Account name / FTP username
    description: str = ""
    ftp_username: str
    ftp_password: str
    broadcast_times: List[str] = []  # List of HH:MM format
    duration: float = 2.5  # Duration in hours
    title_groups: List[TitleDesc] = []
    auth_files_uploaded: bool = False
    last_broadcast: Optional[datetime] = None
    
class AccountCreate(BaseModel):
    name: str
    description: str = ""
    broadcast_times: List[str] = []

class UpdateSchedule(BaseModel):
    broadcast_times: List[str]
    duration: float = 2.5

class AddTitleGroups(BaseModel):
    title_groups: List[TitleDesc]
