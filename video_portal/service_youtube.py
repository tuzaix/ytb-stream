import sys
import os
import random
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Add parent directory to path to import upload_video
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from upload_video import upload_video_once
except ImportError:
    # Handle case where dependencies might be missing in dev env
    logging.warning("Could not import upload_video. Make sure you are in the correct environment.")
    upload_video_once = None

from store import load_accounts, save_account, get_account_auth_dir
from models import Account
import settings 

logger = logging.getLogger(__name__)

# Config for where FTP users are located on disk
# In production, this should match FTP_BASE in create_ftpuser.sh
scheduler = BackgroundScheduler()

def get_video_dir(ftp_username: str) -> str:
    # In a real deployment, this path must be accessible by this service
    return os.path.join(settings.FTP_ROOT_DIR, ftp_username)

def publish_video_task(account_name: str):
    logger.info(f"Starting publish task for account: {account_name}")
    accounts = load_accounts()
    account = accounts.get(account_name)
    
    if not account:
        logger.error(f"Account {account_name} not found during task execution.")
        return

    if not account.copywriting_groups:
        logger.warning(f"No copywriting groups configured for {account_name}. Skipping.")
        return

    # Randomly select copywriting
    copywriting = random.choice(account.copywriting_groups)
    
    # Auth files
    auth_dir = get_account_auth_dir(account.name)
    client_secret = os.path.join(auth_dir, "client_secrets.json")
    token = os.path.join(auth_dir, "token.json")
    
    if not os.path.exists(client_secret) or not os.path.exists(token):
        logger.error(f"Auth files missing for {account_name} in {auth_dir}")
        return

    # Video directory
    video_dir = get_video_dir(account.ftp_username)
    
    # Check if we can access the video directory (might be different on dev machine)
    if not os.path.exists(video_dir):
        logger.warning(f"Video directory {video_dir} does not exist. Assuming dev env or mount issue.")
        # For dev testing, maybe use a temp dir or just log
        # return 
    
    try:
        if upload_video_once:
            logger.info(f"Calling upload_video_once for {account_name} with title: {copywriting.title}")
            result = upload_video_once(
                auth_dir=auth_dir,
                video_dirs=[video_dir],
                title=copywriting.title,
                description=copywriting.description,
                privacy="public", # Assuming public based on "publish" intent
                publish=True
            )
            logger.info(f"Upload result: {result}")
            
            # Update last publish time
            account.last_publish = datetime.now()
            # We need to save the account, but load_accounts returns copies? 
            # store.py logic loads fresh.
            # We should re-load to avoid race conditions or just update this field?
            # For simplicity:
            save_account(account)
        else:
            logger.error("upload_video_once function is not available.")
            
    except Exception as e:
        logger.exception(f"Failed to upload video for {account_name}: {e}")

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
