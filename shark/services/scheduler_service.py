import sys
import os
import random
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import UploadSchedule, YoutubeAccount, MaterialConfig
from ..config import config

# Add parent directory to path to import upload_video
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Try importing upload logic (Mock if fails)
try:
    from upload_video import upload_video_once
except ImportError:
    print("Warning: Could not import upload_video.py. Using mock.")
    def upload_video_once(**kwargs):
        print(f"Mock Upload: {kwargs}")
        return {"status": "success", "id": "mock_video_id"}

class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def add_job(self, schedule_id: int, cron_expression: str):
        """
        Adds or updates a job for the given schedule ID.
        """
        job_id = f"schedule_{schedule_id}"
        
        # Remove existing if any
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        try:
            trigger = CronTrigger.from_crontab(cron_expression)
            self.scheduler.add_job(
                self.execute_upload_task,
                trigger,
                id=job_id,
                args=[schedule_id],
                replace_existing=True
            )
            print(f"[Scheduler] Added job {job_id} with cron {cron_expression}")
        except Exception as e:
            print(f"[Scheduler] Error adding job {job_id}: {e}")

    def remove_job(self, schedule_id: int):
        job_id = f"schedule_{schedule_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            print(f"[Scheduler] Removed job {job_id}")

    def execute_upload_task(self, schedule_id: int):
        """
        The actual task to be executed.
        """
        print(f"[Scheduler] Executing task for schedule {schedule_id}")
        db: Session = SessionLocal()
        try:
            schedule = db.query(UploadSchedule).filter(UploadSchedule.id == schedule_id).first()
            if not schedule or not schedule.is_active:
                print(f"[Scheduler] Schedule {schedule_id} not found or inactive.")
                return

            account = schedule.youtube_account
            material_config = schedule.material_config
            
            if not account or not material_config:
                print("[Scheduler] Account or Material Config missing.")
                return

            # Resolve Title/Desc/Tags
            # In the config model, we stored templates.
            # Logic similar to pick_copywriting in ytb_upload_video_by_account.py
            # If templates contain multiple options (e.g. separated by | or just raw text), we use them.
            # For now, assuming the stored text IS the template.
            
            title = material_config.title_template or ""
            description = material_config.description_template or ""
            tags = material_config.tags or ""
            
            # Construct arguments for upload
            # NOTE: auth_dir and video_dirs need to be determined.
            # Assuming a convention for video_dirs: FTP_BASE/username/
            ftp_base = "/home/ftp" # Defined in shell script
            # In Windows dev, we map it to somewhere else or mock it.
            video_dir = os.path.join(ftp_base, account.account_name)
            
            # Auth dir: where is the token?
            # Assuming standard location for now or configurable
            auth_dir = os.path.dirname(config.UPLOAD_SCRIPT_PATH) # Default to project root
            
            print(f"Uploading for user {account.account_name}...")
            
            result = upload_video_once(
                auth_dir=auth_dir,
                video_dirs=[video_dir], # This might fail on Windows if path doesn't exist
                title=title,
                description=description,
                tags=tags,
                publish=True # Default to published as per requirement implication
            )
            
            # Log result (omitted for brevity, ideally update DB)
            schedule.last_run_at = datetime.now()
            db.commit()
            print(f"Upload Result: {result}")

        except Exception as e:
            print(f"[Scheduler] Error executing task: {e}")
        finally:
            db.close()

scheduler_service = SchedulerService()
