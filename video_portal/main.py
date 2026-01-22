
import os
import shutil
import logging
from typing import List

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from urllib.request import urlopen, Request
import socket

from models import Account, AccountCreate, UpdateSchedule, AddCopywriting, Copywriting
from store import load_accounts, save_account, get_account, delete_account, get_account_auth_dir
from service_ftp import create_ftp_account, delete_ftp_account
from service_youtube import start_scheduler, refresh_scheduler
import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache for public IP
_public_ip_cache = None

def get_directory_size_mb(directory: str) -> float:
    total_size = 0
    try:
        if not os.path.exists(directory):
            return 0.0
        for dirpath, dirnames, filenames in os.walk(directory):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
    except Exception as e:
        logger.error(f"Error calculating size for {directory}: {e}")
        return 0.0
    return round(total_size / (1024 * 1024), 2)

class AccountResponse(Account):
    disk_usage_mb: float = 0.0
    pending_video_count: int = 0

def get_pending_video_count(ftp_username: str) -> int:
    """
    Count videos in {ftp_root}/{username}/video/{subdir}/
    Excluding subdirs ending with 'published'
    """
    account_dir = os.path.join(settings.FTP_ROOT_DIR, ftp_username)
    video_root = os.path.join(account_dir, "video")
    
    if not os.path.exists(video_root):
        return 0
        
    count = 0
    try:
        # Iterate over subdirectories in video_root
        for item in os.listdir(video_root):
            subdir_path = os.path.join(video_root, item)
            
            # We only care about directories
            if not os.path.isdir(subdir_path):
                continue
                
            # Exclude directories with 'published' suffix
            if item.lower().endswith("published"):
                continue
            
            # Count video files in this subdir
            for f in os.listdir(subdir_path):
                if f.lower().endswith(('.mp4', '.mkv', '.mov', '.avi', '.flv', '.webm')):
                    count += 1
    except Exception as e:
        logger.error(f"Error counting videos for {ftp_username}: {e}")
        return 0
    return count

def get_public_ip():
    global _public_ip_cache
    if _public_ip_cache:
        return _public_ip_cache
        
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://checkip.amazonaws.com",
        "http://whatismyip.akamai.com/"
    ]
    
    for url in services:
        try:
            # Set a timeout and a generic User-Agent to avoid blocking
            req = Request(url, headers={'User-Agent': 'curl/7.68.0'})
            with urlopen(req, timeout=5) as response:
                ip = response.read().decode('utf-8').strip()
                if ip:
                    _public_ip_cache = ip
                    return _public_ip_cache
        except Exception as e:
            logger.warning(f"Failed to fetch IP from {url}: {e}")
            continue
            
    logger.error("Failed to fetch public IP from all providers")
    return "127.0.0.1"

app = FastAPI(title="Video Portal Backend")

# Serve Frontend
# Assuming index.html is in ./frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if not os.path.exists(FRONTEND_DIR):
    os.makedirs(FRONTEND_DIR)

# Mount static files if you have assets, but for SPA we often serve index.html for root
# app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth (Simple Mock)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    if token != settings.ACCESS_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return settings.ADMIN_USERNAME

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/system_status")
async def get_system_status(token: str = Depends(oauth2_scheme)):
    # Use the configured FTP root directory to check disk usage
    target_dir = settings.FTP_ROOT_DIR
    if not os.path.exists(target_dir):
        # Fallback to current directory if FTP root doesn't exist yet
        target_dir = "."

    total, used, free = shutil.disk_usage(target_dir)
    
    # Reserve 10GB for system usage
    gb = 1024 ** 3
    reserved_bytes = 10 * gb
    
    # Calculate effective total and free space after reservation
    adjusted_total = max(0, total - reserved_bytes)
    adjusted_free = max(0, free - reserved_bytes)
    
    percent = 0.0
    if adjusted_total > 0:
        percent = round((used / adjusted_total) * 100, 1)

    return {
        "total_gb": round(adjusted_total / gb, 2),
        "used_gb": round(used / gb, 2),
        "free_gb": round(adjusted_free / gb, 2),
        "percent": percent
    }

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == settings.ADMIN_USERNAME and form_data.password == settings.ADMIN_PASSWORD:
        return {"access_token": settings.ACCESS_TOKEN, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Incorrect username or password")

# Account Management

@app.get("/system/info")
def get_system_info(current_user: str = Depends(get_current_user)):
    return {
        "public_ip": get_public_ip(),
        "max_accounts": settings.MAX_ACCOUNTS,
        "max_publish_times": getattr(settings, "MAX_PUBLISH_TIMES_PER_ACCOUNT", 5)
    }

@app.get("/accounts", response_model=List[AccountResponse])
def list_accounts(current_user: str = Depends(get_current_user)):
    accounts = load_accounts().values()
    response = []
    for acc in accounts:
        # Calculate disk usage
        account_dir = os.path.join(settings.FTP_ROOT_DIR, acc.ftp_username)
        size_mb = get_directory_size_mb(account_dir)
        
        # Calculate pending video count
        video_count = get_pending_video_count(acc.ftp_username)
        
        # Create response object
        acc_resp = AccountResponse(**acc.dict(), disk_usage_mb=size_mb, pending_video_count=video_count)
        response.append(acc_resp)
    return response

@app.post("/accounts", response_model=Account)
def create_account(account_in: AccountCreate, current_user: str = Depends(get_current_user)):
    accounts = load_accounts()
    if len(accounts) >= settings.MAX_ACCOUNTS:
        raise HTTPException(status_code=400, detail=f"已达到最大账户数量限制 ({settings.MAX_ACCOUNTS})")

    existing = get_account(account_in.name)
    if existing:
        raise HTTPException(status_code=400, detail="账号已存在")
    
    # 1. Create FTP Account
    # We use the account name as username, but maybe sanitize it?
    # For simplicity, assume account name is safe or use a prefix.
    # But create_ftpuser.sh takes a username.
    ftp_username = account_in.name
    try:
        ftp_password = create_ftp_account(ftp_username)
    except Exception as e:
        logger.error(f"Failed to create FTP account: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create FTP account: {str(e)}")
    
    # 2. Create Account Record
    new_account = Account(
        name=account_in.name,
        description=account_in.description,
        ftp_username=ftp_username,
        ftp_password=ftp_password,
        publish_times=account_in.publish_times
    )
    save_account(new_account)
    
    # Refresh scheduler to pick up new account (if it had a schedule, though initially empty copywriting)
    refresh_scheduler()
    
    return new_account

@app.delete("/accounts/{name}")
def remove_account(name: str, current_user: str = Depends(get_current_user)):
    if not get_account(name):
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Try to delete FTP account first
    try:
        delete_ftp_account(name)
    except Exception as e:
        logger.error(f"Failed to delete FTP account {name}: {e}")
        # Continue with account deletion even if FTP deletion fails
        
    delete_account(name)
    refresh_scheduler()
    return {"message": "Account deleted"}

@app.post("/accounts/{name}/auth")
async def upload_auth_files(
    name: str,
    client_secret: UploadFile = File(...),
    token: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    account = get_account(name)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    auth_dir = get_account_auth_dir(name)
    
    # Save client_secret.json
    client_secret_path = os.path.join(auth_dir, "client_secret.json")
    with open(client_secret_path, "wb") as buffer:
        shutil.copyfileobj(client_secret.file, buffer)
        
    # Save token.json
    token_path = os.path.join(auth_dir, "token.json")
    with open(token_path, "wb") as buffer:
        shutil.copyfileobj(token.file, buffer)
        
    account.auth_files_uploaded = True
    save_account(account)
    
    return {"message": "Auth files uploaded successfully"}

@app.get("/accounts/{name}/logs")
def get_account_logs(name: str, current_user: str = Depends(get_current_user)):
    log_dir = os.path.join(os.path.dirname(__file__), "data", "published_log")
    log_file = os.path.join(log_dir, f"{name}_published.log")
    
    if not os.path.exists(log_file):
        return []
        
    logs = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split(" | ")
                if len(parts) >= 5:
                    logs.append({
                        "timestamp": parts[0],
                        "status": parts[1],
                        "title": parts[2],
                        "message": parts[3],
                        "duration": parts[4]
                    })
                elif len(parts) >= 4:
                    logs.append({
                        "timestamp": parts[0],
                        "status": parts[1],
                        "title": parts[2],
                        "message": " | ".join(parts[3:]),
                        "duration": "-"
                    })
                else:
                    logs.append({
                        "timestamp": "",
                        "status": "RAW",
                        "title": "-",
                        "message": line.strip(),
                        "duration": "-"
                    })
    except Exception as e:
        logger.error(f"Error reading logs for {name}: {e}")
        return []
        
    # Return newest first
    return logs[::-1]

@app.put("/accounts/{name}/copywriting")
def update_copywriting(
    name: str,
    payload: AddCopywriting,
    current_user: str = Depends(get_current_user)
):
    account = get_account(name)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account.copywriting_groups = payload.copywriting_groups
    save_account(account)
    return account

@app.put("/accounts/{name}/schedule")
def update_schedule(
    name: str,
    payload: UpdateSchedule,
    current_user: str = Depends(get_current_user)
):
    account = get_account(name)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account.publish_times = sorted(payload.publish_times)
    save_account(account)
    refresh_scheduler()
    return account

@app.on_event("startup")
def startup_event():
    start_scheduler()
