import json
import os
import shutil
from typing import List, Dict, Optional
from json import JSONDecodeError
from models import Account
import settings

# 系统元数据的目录
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")

def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

def load_accounts() -> Dict[str, Account]:
    _ensure_data_dir()
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            data = json.loads(content)
            return {k: Account(**v) for k, v in data.items()}
    except JSONDecodeError:
        return {}

def save_account(account: Account):
    accounts = load_accounts()
    accounts[account.name] = account
    _save_all(accounts)

def get_account(name: str) -> Optional[Account]:
    accounts = load_accounts()
    return accounts.get(name)

def delete_account(name: str):
    accounts = load_accounts()
    if name in accounts:
        # Remove account directory
        account_dir = os.path.join(settings.FTP_ROOT_DIR, name)
        if os.path.exists(account_dir):
            try:
                shutil.rmtree(account_dir)
            except Exception as e:
                # Log error but continue with account deletion
                print(f"Failed to delete directory {account_dir}: {e}")
        
        del accounts[name]
        _save_all(accounts)

def _save_all(accounts: Dict[str, Account]):
    _ensure_data_dir()
    data = {k: v.dict() for k, v in accounts.items()}
    
    # Atomic write to prevent corruption
    temp_file = ACCOUNTS_FILE + ".tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            # default=str handles datetime objects (e.g. last_publish)
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        # Replace original file with temp file
        if os.path.exists(ACCOUNTS_FILE):
            os.replace(temp_file, ACCOUNTS_FILE)
        else:
            os.rename(temp_file, ACCOUNTS_FILE)
    except Exception as e:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        raise e

def get_account_auth_dir(account_name: str) -> str:
    path = os.path.join(settings.FTP_ROOT_DIR, account_name, "auth2.0")
    if not os.path.exists(path):
        os.makedirs(path)
    return path
