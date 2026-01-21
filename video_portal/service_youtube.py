import sys
import os
import random
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Add parent directory to path to import upload_video
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from upload_video import upload_video_once

from store import load_accounts, save_account, get_account_auth_dir
from models import Account
import settings 

logger = logging.getLogger(__name__)

# Config for where FTP users are located on disk
# In production, this should match FTP_BASE in create_ftpuser.sh
scheduler = BackgroundScheduler()

LOG_DIR = os.path.join(os.path.dirname(__file__), "data", "published_log")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def append_publish_log(account_name: str, status: str, title: str, message: str, duration: str):
    log_file = os.path.join(LOG_DIR, f"{account_name}_published.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Truncate title and message to first 20 chars
    show_max_chars = 30
    short_title = str(title)[:show_max_chars] if title else ""
    short_message = str(message)[:show_max_chars] if message else ""
    duration = duration.split('.')[0] # Remove microseconds

    # log_entry = f"{timestamp} | {status} | {short_title} | {short_message} | {duration}\n"
    log_entry = f"{timestamp} | {status} | {short_title} | - | {duration}\n"
    
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

def get_video_dir(ftp_username: str) -> str:
    # In a real deployment, this path must be accessible by this service
    return os.path.join(settings.FTP_ROOT_DIR, ftp_username, "video")

def publish_video_task(account_name: str):
    start_time = datetime.now()
    logger.info(f"Starting publish task for account: {account_name}")
    accounts = load_accounts()
    account = accounts.get(account_name)
    
    if not account:
        logger.error(f"Account {account_name} not found during task execution.")
        return

    if not account.copywriting_groups:
        logger.warning(f"No copywriting groups configured for {account_name}. Skipping.")
        duration = str(datetime.now() - start_time)
        append_publish_log(account_name, "SKIPPED", "-", "No copywriting groups configured", duration)
        return

    # Randomly select copywriting
    copywriting = random.choice(account.copywriting_groups)
    
    # Auth files
    auth_dir = get_account_auth_dir(account.name)
    client_secret = os.path.join(auth_dir, "client_secrets.json")
    token = os.path.join(auth_dir, "token.json")
    
    if not os.path.exists(client_secret) or not os.path.exists(token):
        logger.error(f"Auth files missing for {account_name} in {auth_dir}")
        duration = str(datetime.now() - start_time)
        append_publish_log(account_name, "FAILED", copywriting.title, "Auth files missing", duration)
        return

    # Video directory
    video_dir = get_video_dir(account.ftp_username)
    
    # Check if we can access the video directory (might be different on dev machine)
    if not os.path.exists(video_dir):
        logger.warning(f"Video directory {video_dir} does not exist. Assuming dev env or mount issue.")
        # For dev testing, maybe use a temp dir or just log
        # return 
    # 获取视频目录下的非_published结尾的目录
    video_dirs = []
    if os.path.exists(video_dir):
        video_dirs = [os.path.join(video_dir, d) for d in os.listdir(video_dir) 
                      if os.path.isdir(os.path.join(video_dir, d)) and not d.endswith("_published")]
    
    try:
        logger.info(f"Calling upload_video_once for {account_name} with title: {copywriting.title}")
        result = upload_video_once(
            auth_dir=auth_dir,
            video_dirs=video_dirs,
            title=copywriting.title,
            description=copywriting.description,
            privacy="public", # Assuming public based on "publish" intent
            publish=True
        )
        logger.info(f"Upload result: {result}")
        
        # Log success
        # The result from upload_video_once is a dict, usually containing uploaded video IDs or status
        # Assuming success if no exception raised
        duration = str(datetime.now() - start_time)
        
        append_publish_log(account_name, "SUCCESS", copywriting.title, f"Result: {result}", duration)

        # Update last publish time
        account.last_publish = datetime.now()
        # We need to save the account, but load_accounts returns copies? 
        # store.py logic loads fresh.
        # We should re-load to avoid race conditions or just update this field?
        # For simplicity:
        save_account(account)
    except Exception as e:
        logger.exception(f"Failed to upload video for {account_name}: {e}")
        duration = str(datetime.now() - start_time)
        append_publish_log(account_name, "ERROR", copywriting.title if copywriting else "-", str(e), duration)

def refresh_scheduler():
    """
    Reloads all schedules from the store.
    """
    scheduler.remove_all_jobs()
    accounts = load_accounts()
    
    for name, account in accounts.items():
        if account.publish_times:
            for time_str in account.publish_times:
                try:
                    hour, minute = map(int, time_str.split(":"))
                    scheduler.add_job(
                        publish_video_task,
                        CronTrigger(hour=hour, minute=minute),
                        args=[name],
                        id=f"publish_{name}_{time_str}",
                        replace_existing=True
                    )
                    logger.info(f"Scheduled task for {name} at {time_str}")
                except ValueError:
                    logger.error(f"Invalid time format for {name}: {time_str}")

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
    refresh_scheduler()
