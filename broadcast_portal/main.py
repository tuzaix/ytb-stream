
import os
import shutil
import logging
from typing import List

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from urllib.request import urlopen, Request

from models import Account, AccountCreate, UpdateSchedule, AddTitleGroups
from store import load_accounts, save_account, get_account, delete_account, get_account_auth_dir
from service_ftp import create_ftp_account, delete_ftp_account
from service_broadcast import start_scheduler, refresh_scheduler
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
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
    except Exception as e:
        logger.error(f"Error calculating size for {directory}: {e}")
        return 0.0
    return round(total_size / (1024 * 1024), 2)

def get_video_file_count(account_dir: str) -> int:
    live_dir = os.path.join(account_dir, "live")
    if not os.path.exists(live_dir):
        return 0
    
    count = 0
    video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.ts'}
    
    # User requirement: "live目录下的下一级目录内"
    # We will look into subdirectories of live/
    try:
        # List items in live dir
        items = os.listdir(live_dir)
        for item in items:
            item_path = os.path.join(live_dir, item)
            if os.path.isdir(item_path):
                # Look for videos in this subdirectory
                for f in os.listdir(item_path):
                    if os.path.isfile(os.path.join(item_path, f)):
                        ext = os.path.splitext(f)[1].lower()
                        if ext in video_extensions:
                            count += 1
    except Exception as e:
        logger.error(f"Error counting videos in {live_dir}: {e}")
        return 0
        
    return count

class AccountResponse(Account):
    disk_usage_mb: float = 0.0
    video_count: int = 0

def get_public_ip():
    global _public_ip_cache
    if _public_ip_cache:
        return _public_ip_cache
        
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://checkip.amazonaws.com"
    ]
    
    for url in services:
        try:
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

app = FastAPI(title="Broadcast Portal Backend")

# Serve Frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if not os.path.exists(FRONTEND_DIR):
    os.makedirs(FRONTEND_DIR)

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
    target_dir = settings.FTP_ROOT_DIR
    if not os.path.exists(target_dir):
        target_dir = "."

    total, used, free = shutil.disk_usage(target_dir)
    gb = 1024 ** 3
    reserved_bytes = 10 * gb
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
        "max_broadcast_times": settings.MAX_BROADCAST_TIMES_PER_ACCOUNT,
        "max_accounts": settings.MAX_ACCOUNTS
    }

@app.get("/accounts", response_model=List[AccountResponse])
def list_accounts(current_user: str = Depends(get_current_user)):
    accounts = load_accounts().values()
    response = []
    for acc in accounts:
        account_dir = os.path.join(settings.FTP_ROOT_DIR, acc.ftp_username)
        size_mb = get_directory_size_mb(account_dir)
        video_cnt = get_video_file_count(account_dir)
        acc_resp = AccountResponse(**acc.dict(), disk_usage_mb=size_mb, video_count=video_cnt)
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
    
    ftp_username = account_in.name
    try:
        ftp_password = create_ftp_account(ftp_username)
    except Exception as e:
        logger.error(f"Failed to create FTP account: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create FTP account: {str(e)}")
    
    new_account = Account(
        name=account_in.name,
        description=account_in.description,
        ftp_username=ftp_username,
        ftp_password=ftp_password,
        broadcast_times=account_in.broadcast_times
    )
    save_account(new_account)
    refresh_scheduler()
    return new_account

@app.delete("/accounts/{name}")
def remove_account(name: str, current_user: str = Depends(get_current_user)):
    if not get_account(name):
        raise HTTPException(status_code=404, detail="Account not found")
    
    try:
        delete_ftp_account(name)
    except Exception as e:
        logger.error(f"Failed to delete FTP account {name}: {e}")
        
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
    
    with open(os.path.join(auth_dir, "client_secret.json"), "wb") as buffer:
        shutil.copyfileobj(client_secret.file, buffer)
        
    with open(os.path.join(auth_dir, "token.json"), "wb") as buffer:
        shutil.copyfileobj(token.file, buffer)
        
    account.auth_files_uploaded = True
    save_account(account)
    
    return {"message": "Auth files uploaded successfully"}

@app.get("/accounts/{name}/logs")
def get_account_logs(name: str, current_user: str = Depends(get_current_user)):
    log_dir = os.path.join(os.path.dirname(__file__), "data", "broadcast_log")
    log_file = os.path.join(log_dir, f"{name}_broadcast.log")
    
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
        
    return logs[::-1]

@app.put("/accounts/{name}/title_groups")
def update_title_groups(name: str, payload: AddTitleGroups, current_user: str = Depends(get_current_user)):
    account = get_account(name)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account.title_groups = payload.title_groups
    save_account(account)
    return account

@app.put("/accounts/{name}/schedule")
def update_schedule(name: str, schedule: UpdateSchedule, current_user: str = Depends(get_current_user)):
    account = get_account(name)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Check for duplicates
    if len(schedule.broadcast_times) != len(set(schedule.broadcast_times)):
        raise HTTPException(status_code=400, detail="不允许设置重复的直播时间")

    # Check for max broadcast times
    if len(schedule.broadcast_times) > settings.MAX_BROADCAST_TIMES_PER_ACCOUNT:
        raise HTTPException(status_code=400, detail=f"最多只能设置 {settings.MAX_BROADCAST_TIMES_PER_ACCOUNT} 个直播时间")

    # Check for duration limit
    if schedule.duration > 3:
        raise HTTPException(status_code=400, detail="直播时长最长只能设置到 3 小时")

    # Check for time interval
    if len(schedule.broadcast_times) > 1:
        sorted_times = sorted(schedule.broadcast_times)
        
        def to_minutes(t_str):
            h, m = map(int, t_str.split(':'))
            return h * 60 + m
            
        minutes_list = [to_minutes(t) for t in sorted_times]
        duration_minutes = schedule.duration * 60
        
        for i in range(len(minutes_list)):
            current = minutes_list[i]
            next_idx = (i + 1) % len(minutes_list)
            next_val = minutes_list[next_idx]
            
            if next_idx == 0:
                next_val += 24 * 60
            
            if next_val - current <= duration_minutes:
                 t1 = sorted_times[i]
                 t2 = sorted_times[next_idx]
                 raise HTTPException(status_code=400, detail=f"直播时间间隔冲突：{t1} 与 {t2} 间隔过短（需大于 {schedule.duration} 小时）")

    account.broadcast_times = sorted(schedule.broadcast_times)
    account.duration = schedule.duration
    save_account(account)
    
    refresh_scheduler()
    return {"message": "Schedule updated"}

@app.on_event("startup")
def startup_event():
    start_scheduler()
