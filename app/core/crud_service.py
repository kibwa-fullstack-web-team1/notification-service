from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

# Import models and schemas
from app import models
from app import schemas


def def create_report(db: Session, report: schemas.ReportCreate) -> models.Report:
    kst_now = datetime.utcnow() + timedelta(hours=9)
    db_report = models.Report(
        user_id=report.user_id, 
        report_data=report.report_data,
        report_date=kst_now
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

# NotificationLog CRUD operations

def create_notification_log(db: Session, log: schemas.NotificationLogCreate) -> models.NotificationLog:
    """
    Create a new notification log entry.
    """
    db_log = models.NotificationLog(
        triggering_user_id=log.triggering_user_id,
        recipient_user_id=log.recipient_user_id,
        message=log.message,
        status=log.status,
        provider_response=log.provider_response
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_notification_logs(
    db: Session,
    recipient_user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.NotificationLog]:
    """
    Retrieve notification logs, with optional filtering by recipient user ID.
    """
    query = db.query(models.NotificationLog).order_by(models.NotificationLog.sent_at.desc())
    if recipient_user_id:
        query = query.filter(models.NotificationLog.recipient_user_id == recipient_user_id)
    
    return query.offset(skip).limit(limit).all()
