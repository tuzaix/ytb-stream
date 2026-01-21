
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

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == settings.ADMIN_USERNAME and form_data.password == settings.ADMIN_PASSWORD:
        return {"access_token": settings.ACCESS_TOKEN, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Incorrect username or password")

# Account Management

@app.get("/system/info")
def get_system_info(current_user: str = Depends(get_current_user)):
    return {"public_ip": get_public_ip()}

@app.get("/accounts", response_model=List[Account])
def list_accounts(current_user: str = Depends(get_current_user)):
    return list(load_accounts().values())

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
    client_secret_path = os.path.join(auth_dir, "client_secrets.json")
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
                if len(parts) >= 4:
                    logs.append({
                        "timestamp": parts[0],
                        "status": parts[1],
                        "title": parts[2],
                        "message": " | ".join(parts[3:])
                    })
                else:
                    logs.append({
                        "timestamp": "",
                        "status": "RAW",
                        "title": "-",
                        "message": line.strip()
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
