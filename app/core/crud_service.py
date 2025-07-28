from sqlalchemy.orm import Session
from app.models.report import Report
from app.schemas.report_schema import ReportCreate
from datetime import datetime, timedelta

def create_report(db: Session, report: ReportCreate):
    kst_now = datetime.utcnow() + timedelta(hours=9)
    db_report = Report(
        user_id=report.user_id, 
        report_data=report.report_data, # report_data 저장
        report_date=kst_now
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

# 필요하다면 다른 CRUD 함수 (read, update, delete)도 여기에 추가할 수 있습니다.