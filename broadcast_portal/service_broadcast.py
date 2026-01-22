import sys
import os
import random
import logging
import multiprocessing
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger

from store import load_accounts, save_account, get_account_auth_dir
from models import Account
import settings 

# Add parent directory to path to import upload_stream
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import upload_stream

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

def get_random_video(account_name: str):
    account_dir = os.path.join(settings.FTP_ROOT_DIR, account_name)
    live_dir = os.path.join(account_dir, "live")
    if not os.path.exists(live_dir):
        return None
    
    videos = []
    video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.ts'}
    
    try:
        # Search in subdirectories
        for item in os.listdir(live_dir):
            item_path = os.path.join(live_dir, item)
            if os.path.isdir(item_path):
                for f in os.listdir(item_path):
                    if os.path.isfile(os.path.join(item_path, f)):
                        ext = os.path.splitext(f)[1].lower()
                        if ext in video_extensions:
                            videos.append(os.path.join(item_path, f))
        
        # Also search in root of live_dir
        # for f in os.listdir(live_dir):
        #      if os.path.isfile(os.path.join(live_dir, f)):
        #         ext = os.path.splitext(f)[1].lower()
        #         if ext in video_extensions:
        #             videos.append(os.path.join(live_dir, f))

    except Exception:
        pass
    
    if not videos:
        return None
    
    return random.choice(videos)

def get_random_cover(account_name: str):
    account_dir = os.path.join(settings.FTP_ROOT_DIR, account_name)
    cover_dir = os.path.join(account_dir, "live_cover")
    if not os.path.exists(cover_dir):
        return None
    
    covers = []
    try:
        for f in os.listdir(cover_dir):
            if os.path.isfile(os.path.join(cover_dir, f)) and f.lower().endswith(('.jpg', '.png')):
                covers.append(os.path.join(cover_dir, f))
    except Exception:
        pass

    return random.choice(covers) if covers else None

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

    # Select Video
    video_file = get_random_video(account_name)
    if not video_file:
        logger.error(f"No valid video files found for {account_name}")
        append_broadcast_log(account_name, "FAILED", title, "No video files found", "0:00:00")
        return

    # Select Cover (Thumbnail)
    cover_file = get_random_cover(account_name)
    
    # Log file for this broadcast run
    log_file = os.path.join(LOG_DIR, f"{account_name}_broadcast.log")

    try:
        logger.info(f"Launching broadcast process for {account_name}")
        
        # Use multiprocessing to run the broadcast without blocking the scheduler
        p = multiprocessing.Process(
            target=upload_stream.run_broadcast,
            kwargs={
                "auth_dir": auth_dir,
                "video_file": video_file,
                "title": title,
                "description": description,
                "privacy_status": "public",
                "duration": float(account.duration),
                "thumbnail": cover_file,
                "log_file": log_file
            }
        )
        p.start()
        
        append_broadcast_log(account_name, "STARTED", title, f"PID: {p.pid} | Video: {os.path.basename(video_file)}", "0:00:00")

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
