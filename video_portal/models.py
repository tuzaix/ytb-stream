from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class Copywriting(BaseModel):
    title: str
    description: str

class Account(BaseModel):
    name: str  # YouTube account name
    description: str = ""
    ftp_username: str
    ftp_password: str
    publish_times: List[str] = []  # List of HH:MM format
    copywriting_groups: List[Copywriting] = []
    auth_files_uploaded: bool = False
    last_publish: Optional[datetime] = None
    
class AccountCreate(BaseModel):
    name: str
    description: str = ""
    publish_times: List[str] = []

class UpdateSchedule(BaseModel):
    publish_times: List[str]

class AddCopywriting(BaseModel):
    copywriting_groups: List[Copywriting]
