import os
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User, YoutubeAccount, MaterialConfig, UploadSchedule, ScheduleType, IntervalUnit
from ..schemas import (
    YoutubeAccountCreate, YoutubeAccountOut, 
    MaterialConfigCreate, MaterialConfigOut, PaginatedMaterialConfigOut,
    ScheduleCreate, ScheduleOut, PaginatedScheduleOut
)
from .auth import get_current_user
from ..services.ftp_service import ftp_service
from ..services.scheduler_service import scheduler_service
from ..config import config

router = APIRouter(prefix="/youtube", tags=["youtube"])

def save_auth_file(account_name: str, filename: str, content: bytes):
    """Save auth file to configured upload directory"""
    # Create account-specific directory
    account_dir = os.path.join(config.UPLOAD_DIR, account_name)
    os.makedirs(account_dir, exist_ok=True)
    
    file_path = os.path.join(account_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path

# --- Youtube Accounts (FTP) ---

@router.post("/accounts", response_model=YoutubeAccountOut)
async def create_youtube_account(
    desired_username: str = Form(...),
    client_secret_file: UploadFile = File(...),
    token_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Check membership limits
    if not current_user.membership:
        raise HTTPException(status_code=400, detail="No membership active")
    
    current_count = len(current_user.youtube_accounts)
    max_accounts = current_user.membership.max_youtube_accounts
    
    if current_count >= max_accounts:
        raise HTTPException(status_code=403, detail=f"Membership limit reached. Max {max_accounts} accounts.")

    # Check username uniqueness
    existing = db.query(YoutubeAccount).filter(YoutubeAccount.account_name == desired_username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Account name already exists")

    # Read file contents
    try:
        client_secret_content = await client_secret_file.read()
        token_content = await token_file.read()
        
        # Ensure they are valid strings (utf-8)
        client_secret_str = client_secret_content.decode("utf-8")
        token_str = token_content.decode("utf-8")
        
        # Save files to configured directory
        save_auth_file(desired_username, "client_secret.json", client_secret_content)
        save_auth_file(desired_username, "token.json", token_content)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid file content or write error: {str(e)}")

    # Create FTP User
    try:
        # Use membership details for quota and speed
        quota_mb = current_user.membership.ftp_storage_mb
        speed_kbps = current_user.membership.ftp_speed_kbps
        
        ftp_password = ftp_service.create_user(
            username=desired_username,
            quota_mb=quota_mb,
            speed_kbps=speed_kbps
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create FTP user: {str(e)}")

    # Save to DB
    new_account = YoutubeAccount(
        user_id=current_user.id,
        account_name=desired_username,
        ftp_password=ftp_password,
        client_secret_content=client_secret_str,
        token_content=token_str
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    # Populate transient fields for response
    new_account.ftp_host = config.FTP_HOST
    new_account.ftp_port = config.FTP_PORT
    
    return new_account

@router.get("/accounts", response_model=List[YoutubeAccountOut])
def list_youtube_accounts(current_user: User = Depends(get_current_user)):
    accounts = current_user.youtube_accounts
    for acc in accounts:
        acc.ftp_host = config.FTP_HOST
        acc.ftp_port = config.FTP_PORT
    return accounts

@router.put("/accounts/{account_id}/auth", response_model=YoutubeAccountOut)
async def update_youtube_account_auth(
    account_id: int,
    client_secret_file: UploadFile = File(...),
    token_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(YoutubeAccount).filter(YoutubeAccount.id == account_id, YoutubeAccount.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Read file contents
    try:
        client_secret_content = await client_secret_file.read()
        token_content = await token_file.read()
        
        # Ensure they are valid strings (utf-8)
        client_secret_str = client_secret_content.decode("utf-8")
        token_str = token_content.decode("utf-8")
        
        # Save files to configured directory (overwrite existing)
        save_auth_file(account.account_name, "client_secret.json", client_secret_content)
        save_auth_file(account.account_name, "token.json", token_content)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid file content or write error: {str(e)}")

    account.client_secret_content = client_secret_str
    account.token_content = token_str
    
    db.commit()
    db.refresh(account)
    
    # Populate transient fields for response
    account.ftp_host = config.FTP_HOST
    account.ftp_port = config.FTP_PORT
    
    return account

@router.delete("/accounts/{account_id}", status_code=204)
def delete_youtube_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(YoutubeAccount).filter(YoutubeAccount.id == account_id, YoutubeAccount.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Delete FTP user
    try:
        ftp_service.delete_user(account.account_name)
    except Exception as e:
        # Log error but proceed with DB deletion to avoid zombie records
        print(f"Failed to delete FTP user {account.account_name}: {e}")

    # Delete auth files directory
    try:
        account_dir = os.path.join(config.UPLOAD_DIR, account.account_name)
        if os.path.exists(account_dir):
            import shutil
            shutil.rmtree(account_dir)
    except Exception as e:
        print(f"Failed to delete account directory {account.account_name}: {e}")

    # Delete related records (Schedules first, then MaterialConfigs, then Account) to avoid FK constraints
    db.query(UploadSchedule).filter(UploadSchedule.youtube_account_id == account.id).delete()
    db.query(MaterialConfig).filter(MaterialConfig.youtube_account_id == account.id).delete()

    db.delete(account)
    db.commit()
    return

# --- Material Configs ---

@router.post("/accounts/{account_id}/materials", response_model=MaterialConfigOut)
def create_material_config(
    account_id: int,
    config_in: MaterialConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(YoutubeAccount).filter(YoutubeAccount.id == account_id, YoutubeAccount.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    new_config = MaterialConfig(
        youtube_account_id=account.id,
        group_name=config_in.group_name,
        material_type=config_in.material_type,
        title_template=config_in.title_template,
        description_template=config_in.description_template,
        tags=config_in.tags,
        is_active=config_in.is_active
    )
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    return new_config

@router.get("/accounts/{account_id}/materials", response_model=PaginatedMaterialConfigOut)
def list_materials(
    account_id: int,
    skip: int = 0,
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(YoutubeAccount).filter(YoutubeAccount.id == account_id, YoutubeAccount.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    query = db.query(MaterialConfig).filter(MaterialConfig.youtube_account_id == account_id)
    total = query.count()
    items = query.order_by(MaterialConfig.created_at.desc()).offset(skip).limit(limit).all()
    
    return {"total": total, "items": items}

@router.delete("/materials/{material_id}")
def delete_material_config(
    material_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify ownership via join
    material = db.query(MaterialConfig).join(YoutubeAccount).filter(
        MaterialConfig.id == material_id, 
        YoutubeAccount.user_id == current_user.id
    ).first()
    
    if not material:
        raise HTTPException(status_code=404, detail="Material config not found")
    
    # Check if any schedules depend on this material
    linked_schedules = db.query(UploadSchedule).filter(UploadSchedule.material_config_id == material.id).count()
    if linked_schedules > 0:
         raise HTTPException(status_code=400, detail="Cannot delete material config used by existing schedules. Please delete the schedules first.")

    db.delete(material)
    db.commit()
    return {"detail": "Material config deleted"}

# --- Schedules ---

@router.post("/accounts/{account_id}/schedules", response_model=ScheduleOut)
def create_schedule(
    account_id: int,
    schedule_in: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(YoutubeAccount).filter(YoutubeAccount.id == account_id, YoutubeAccount.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Verify material config belongs to account
    material = db.query(MaterialConfig).filter(MaterialConfig.id == schedule_in.material_config_id, MaterialConfig.youtube_account_id == account.id).first()
    if not material:
        raise HTTPException(status_code=400, detail="Material Config not found or does not belong to this account")

    # Validate schedule fields
    if schedule_in.schedule_type == ScheduleType.INTERVAL:
        if not schedule_in.interval_value or not schedule_in.interval_unit:
            raise HTTPException(status_code=400, detail="Interval value and unit are required for interval schedule")
    elif schedule_in.schedule_type == ScheduleType.DAILY:
        if not schedule_in.run_time:
            raise HTTPException(status_code=400, detail="Run time is required for daily schedule")
    elif schedule_in.schedule_type == ScheduleType.WEEKLY:
        if not schedule_in.run_time or not schedule_in.weekdays:
            raise HTTPException(status_code=400, detail="Run time and weekdays are required for weekly schedule")
    elif schedule_in.schedule_type == ScheduleType.MONTHLY:
        if not schedule_in.run_time or not schedule_in.month_day:
            raise HTTPException(status_code=400, detail="Run time and month day are required for monthly schedule")

    new_schedule = UploadSchedule(
        youtube_account_id=account.id,
        material_config_id=schedule_in.material_config_id,
        schedule_type=schedule_in.schedule_type,
        interval_value=schedule_in.interval_value,
        interval_unit=schedule_in.interval_unit,
        run_time=schedule_in.run_time,
        weekdays=schedule_in.weekdays,
        month_day=schedule_in.month_day,
        is_active=schedule_in.is_active
    )
    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)

    # Add to Scheduler
    if new_schedule.is_active:
        scheduler_service.add_job(new_schedule)

    return new_schedule

@router.get("/accounts/{account_id}/schedules", response_model=PaginatedScheduleOut)
def list_schedules(
    account_id: int,
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(YoutubeAccount).filter(YoutubeAccount.id == account_id, YoutubeAccount.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    query = db.query(UploadSchedule).filter(UploadSchedule.youtube_account_id == account_id)
    total = query.count()
    items = query.order_by(UploadSchedule.created_at.desc()).offset(skip).limit(limit).all()
    
    return {"total": total, "items": items}

@router.delete("/schedules/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    schedule = db.query(UploadSchedule).join(YoutubeAccount).filter(UploadSchedule.id == schedule_id, YoutubeAccount.user_id == current_user.id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    scheduler_service.remove_job(schedule_id)
    db.delete(schedule)
    db.commit()
    return {"detail": "Schedule deleted"}
