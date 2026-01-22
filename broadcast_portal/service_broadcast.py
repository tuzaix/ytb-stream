import sys
import os
import random
import logging
import subprocess
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger

from store import load_accounts, save_account, get_account_auth_dir
from models import Account
import settings 

logger = logging.getLogger(__name__)

executors = {
    'default': ThreadPoolExecutor(settings.SCHEDULER_MAX_WORKERS)
}
scheduler = BackgroundScheduler(executors=executors)

LOG_DIR = os.path.join(os.path.dirname(__file__), "data", "broadcast_log")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def append_broadcast_log(account_name: str, status: str, title: str, message: str, duration: str):
    log_file = os.path.join(LOG_DIR, f"{account_name}_broadcast.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Truncate title and message to first 20 chars for log readability
    show_max_chars = 30
    short_title = str(title)[:show_max_chars] if title else ""
    short_message = str(message)[:show_max_chars] if message else ""
    duration = duration.split('.')[0] # Remove microseconds

    log_entry = f"{timestamp} | {status} | {short_title} | {short_message} | {duration}\n"
    
    lines = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            logger.error(f"Failed to read log for {account_name}: {e}")
    
    lines.append(log_entry)
    
    # Keep only the last 50 lines
    if len(lines) > 50:
        lines = lines[-50:]
        
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception as e:
        logger.error(f"Failed to write log for {account_name}: {e}")

def broadcast_task(account_name: str, time_str: str):
    start_time = datetime.now()
    logger.info(f"Starting broadcast task for account: {account_name} at {time_str}")
    accounts = load_accounts()
    account = accounts.get(account_name)
    
    if not account:
        logger.error(f"Account {account_name} not found during task execution.")
        return

    # Check auth files
    auth_dir = get_account_auth_dir(account.name)
    client_secret = os.path.join(auth_dir, "client_secret.json")
    token = os.path.join(auth_dir, "token.json")
    
    if not os.path.exists(client_secret) or not os.path.exists(token):
        logger.error(f"Auth files missing for {account_name} in {auth_dir}")
        append_broadcast_log(account_name, "FAILED", "-", "Auth files missing", "0:00:00")
        return

    # Select Title/Description
    if not account.title_groups:
        logger.warning(f"No title groups configured for {account_name}. Using defaults.")
        title = f"Live Stream {datetime.now().strftime('%Y-%m-%d')}"
        description = "Live streaming..."
    else:
        group = random.choice(account.title_groups)
        title = group.title
        description = group.description

    # Prepare arguments
    # Usage: $0 <类别> <标题> <直播时段:2/7/10/22> [直播时长：默认是2.5h] [直播时间:2025-10-20] [直播说明]
    category = account.name
    timescope = time_str
    duration_arg = str(account.duration)
    run_date = datetime.now().strftime("%Y-%m-%d")
    
    # Construct command
    # We use "bash" explicitly
    cmd = [
        "bash",
        settings.BROADCAST_SCRIPT_PATH,
        category,
        title,
        timescope,
        duration_arg,
        run_date,
        description
    ]
    
    try:
        if os.name == 'nt':
            # Mock execution on Windows
            logger.info(f"[MOCK] Executing command: {' '.join(cmd)}")
            append_broadcast_log(account_name, "MOCK_SUCCESS", title, "Windows Mock Execution", "0:00:00")
        else:
            logger.info(f"Executing command: {' '.join(cmd)}")
            # Run in background (Popen)
            # We want to detach it so it keeps running even if this thread finishes
            # start_new_session=True creates a new process group
            kwargs = {}
            if os.name != 'nt':
                kwargs['start_new_session'] = True
            
            proc = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                **kwargs
            )
            
            # We don't wait for it to finish because it's a live stream (hours)
            # But we can check if it failed immediately?
            # Maybe wait 1 second?
            try:
                outs, errs = proc.communicate(timeout=1)
                if proc.returncode != 0:
                    logger.error(f"Broadcast script failed immediately: {errs}")
                    append_broadcast_log(account_name, "FAILED", title, f"Script Error: {errs}", "0:00:00")
                    return
            except subprocess.TimeoutExpired:
                # This is good! It's running.
                pass
            
            append_broadcast_log(account_name, "STARTED", title, f"PID: {proc.pid}", "0:00:00")

        # Update last broadcast time
        account.last_broadcast = datetime.now()
        save_account(account)
        
    except Exception as e:
        logger.exception(f"Failed to start broadcast for {account_name}: {e}")
        append_broadcast_log(account_name, "ERROR", title, str(e), "0:00:00")

def refresh_scheduler():
    """
    Reloads all schedules from the store.
    """
    scheduler.remove_all_jobs()
    accounts = load_accounts()
    
    for name, account in accounts.items():
        if account.broadcast_times:
            for time_str in account.broadcast_times:
                try:
                    hour, minute = map(int, time_str.split(":"))
                    scheduler.add_job(
                        broadcast_task,
                        CronTrigger(hour=hour, minute=minute),
                        args=[name, time_str],
                        id=f"broadcast_{name}_{time_str}",
                        replace_existing=True
                    )
                    logger.info(f"Scheduled broadcast for {name} at {time_str}")
                except ValueError:
                    logger.error(f"Invalid time format for {name}: {time_str}")

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
    refresh_scheduler()
