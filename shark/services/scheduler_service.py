import sys
import os
import random
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import UploadSchedule, YoutubeAccount, MaterialConfig, ScheduleType, IntervalUnit
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

    def add_job(self, schedule: UploadSchedule):
        """
        Adds or updates a job for the given schedule.
        """
        job_id = f"schedule_{schedule.id}"
        
        # Remove existing if any
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        try:
            trigger = None
            if schedule.schedule_type == ScheduleType.INTERVAL:
                minutes = 0
                hours = 0
                if schedule.interval_unit == IntervalUnit.MINUTES:
                    minutes = schedule.interval_value
                elif schedule.interval_unit == IntervalUnit.HOURS:
                    hours = schedule.interval_value
                
                # Ensure at least some interval
                if minutes == 0 and hours == 0:
                    print(f"[Scheduler] Invalid interval for job {job_id}")
                    return

                trigger = IntervalTrigger(minutes=minutes, hours=hours)
            
            elif schedule.schedule_type == ScheduleType.DAILY:
                if not schedule.run_time:
                    print(f"[Scheduler] Missing run_time for DAILY job {job_id}")
                    return
                hour, minute = schedule.run_time.split(":")
                trigger = CronTrigger(hour=hour, minute=minute)
            
            elif schedule.schedule_type == ScheduleType.WEEKLY:
                if not schedule.run_time or not schedule.weekdays:
                    print(f"[Scheduler] Missing run_time or weekdays for WEEKLY job {job_id}")
                    return
                hour, minute = schedule.run_time.split(":")
                trigger = CronTrigger(day_of_week=schedule.weekdays, hour=hour, minute=minute)
            
            elif schedule.schedule_type == ScheduleType.MONTHLY:
                if not schedule.run_time or not schedule.month_day:
                    print(f"[Scheduler] Missing run_time or month_day for MONTHLY job {job_id}")
                    return
                hour, minute = schedule.run_time.split(":")
                trigger = CronTrigger(day=schedule.month_day, hour=hour, minute=minute)

            if trigger:
                job = self.scheduler.add_job(
                    self.execute_upload_task,
                    trigger,
                    id=job_id,
                    args=[schedule.id],
                    replace_existing=True
                )
                print(f"[Scheduler] Added job {job_id} type {schedule.schedule_type}")
                
                # Update next_run_at
                if job.next_run_time:
                    self.update_next_run_at(schedule.id, job.next_run_time)
            else:
                 print(f"[Scheduler] Could not determine trigger for job {job_id}")

        except Exception as e:
            print(f"[Scheduler] Error adding job {job_id}: {e}")

    def update_next_run_at(self, schedule_id: int, next_run_time: datetime):
        db = SessionLocal()
        try:
            schedule = db.query(UploadSchedule).filter(UploadSchedule.id == schedule_id).first()
            if schedule:
                schedule.next_run_at = next_run_time
                db.commit()
                # print(f"[Scheduler] Updated next_run_at for {schedule_id} to {next_run_time}")
        except Exception as e:
            print(f"[Scheduler] Failed to update next_run_at: {e}")
        finally:
            db.close()

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
