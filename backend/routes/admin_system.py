import subprocess
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database.connection import get_db, Settings
from models.domain import AuditLog, MaintenanceSchedule, BackupRecord, User
from schemas.audit import AuditLogOut, MaintenanceScheduleOut, MaintenanceScheduleBase, BackupRecordOut
from auth.security import get_current_user
from typing import List

router = APIRouter()

def log_audit(db: Session, admin_id: int, action: str, resource: str):
    log = AuditLog(admin_id=admin_id, action=action, resource=resource, ip_address="127.0.0.1")
    db.add(log)

@router.get("/audit-logs", response_model=List[AuditLogOut])
def get_audit_logs(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()
    result = []
    for log in logs:
        admin = db.query(User).filter(User.id == log.admin_id).first()
        log_dict = log.__dict__.copy()
        log_dict["admin_name"] = admin.full_name if admin else "Unknown"
        result.append(log_dict)
    return result

@router.get("/maintenance", response_model=MaintenanceScheduleOut)
def get_maintenance(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    schedule = db.query(MaintenanceSchedule).first()
    if not schedule:
        schedule = MaintenanceSchedule()
        db.add(schedule)
        db.commit()
    return schedule

@router.post("/maintenance", response_model=MaintenanceScheduleOut)
def toggle_maintenance(data: MaintenanceScheduleBase, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    schedule = db.query(MaintenanceSchedule).first()
    schedule.is_active = data.is_active
    schedule.message = data.message
    schedule.start_time = data.start_time
    schedule.end_time = data.end_time
    schedule.whitelist_ips = data.whitelist_ips
    db.commit()
    log_audit(db, current_user.id, f"{'Enabled' if data.is_active else 'Disabled'} Maintenance Mode", "System")
    return schedule

@router.get("/backups", response_model=List[BackupRecordOut])
def get_backups(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    backups = db.query(BackupRecord).order_by(BackupRecord.created_at.desc()).all()
    result = []
    for b in backups:
        admin = db.query(User).filter(User.id == b.created_by).first()
        b_dict = b.__dict__.copy()
        b_dict["creator_name"] = admin.full_name if admin else "System"
        result.append(b_dict)
    return result

def run_mysqldump(db: Session, backup_id: int, admin_id: int):
    import shutil
    if not shutil.which("mysqldump"):
        backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
        backup.status = "FAILED: mysqldump not found"
        db.commit()
        return

    # VERY basic parsing of DATABASE_URL for mysqldump
    # Expected format: mysql+pymysql://user:pass@host:port/dbname
    try:
        from urllib.parse import urlparse
        # URL usually starts with mysql+pymysql://
        settings = Settings()
        db_url = settings.DATABASE_URL.replace("mysql+pymysql://", "mysql://")
        parsed = urlparse(db_url)
        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        db_name = parsed.path[1:]

        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        filename = f"terravyn_backup_{timestamp}.sql"
        storage_path = os.path.join(os.getcwd(), "storage", "backups")
        os.makedirs(storage_path, exist_ok=True)
        file_path = os.path.join(storage_path, filename)

        cmd = ["mysqldump", "-u", user, f"-p{password}", "-h", host, db_name]
        with open(file_path, "w") as f:
            subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True)

        file_size = os.path.getsize(file_path)
        
        backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
        backup.file_name = filename
        backup.file_size = file_size
        backup.status = "COMPLETED"
        db.commit()

        log_audit(db, admin_id, f"Created Database Backup {filename}", "Backup")
    except Exception as e:
        backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
        backup.status = f"FAILED: {str(e)}"
        db.commit()

@router.post("/backups", response_model=BackupRecordOut)
def create_backup(background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    import shutil
    if not shutil.which("mysqldump"):
        raise HTTPException(status_code=500, detail="MySQL backup utility (mysqldump) is not available on this server. Please contact the system administrator.")

    backup = BackupRecord(file_name="Pending...", file_size=0, status="IN_PROGRESS", created_by=current_user.id)
    db.add(backup)
    db.commit()
    db.refresh(backup)

    # In a real app we might pass a fresh DB session or connection to background task
    background_tasks.add_task(run_mysqldump, db, backup.id, current_user.id)

    b_dict = backup.__dict__.copy()
    b_dict["creator_name"] = current_user.full_name
    return b_dict

@router.delete("/backups/{backup_id}")
def delete_backup(backup_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    file_path = os.path.join(os.getcwd(), "storage", "backups", backup.file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.delete(backup)
    db.commit()
    log_audit(db, current_user.id, f"Deleted Backup {backup.file_name}", "Backup")
    return {"message": "Backup deleted successfully"}
