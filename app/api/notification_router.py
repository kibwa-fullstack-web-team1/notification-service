from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core import aws_notification_service, crud_service
from app.helper import verification_helper, notification_helper
from app import schemas
from app.utils.db import get_db

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

@router.post("/send-email")
async def send_email_notification(request: schemas.EmailRequest):
    success = aws_notification_service.send_email(
        request.sender_email,
        request.recipient_email,
        request.subject,
        request.body
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="이메일 발송에 실패했습니다.")
    return {"message": "이메일이 성공적으로 발송되었습니다."}

@router.post("/send-sms")
async def send_sms_notification(request: schemas.SmsRequest):
    success = aws_notification_service.send_sms(
        request.phone_number,
        request.message
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="SMS 발송에 실패했습니다.")
    return {"message": "SMS가 성공적으로 발송되었습니다."}

@router.post("/phone/send-code")
async def send_phone_verification_code(request: schemas.PhoneNumberRequest):
    """전화번호 인증 코드를 생성하고 SMS로 발송합니다."""
    code = verification_helper.generate_verification_code(request.phone_number)
    success = aws_notification_service.send_verification_sms(request.phone_number, code)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="인증 코드 발송에 실패했습니다.")
    return {"message": "인증 코드가 성공적으로 발송되었습니다."}

@router.post("/phone/verify-code")
async def verify_phone_code(request: schemas.VerificationCodeRequest):
    """제출된 인증 코드를 검증합니다."""
    success = verification_helper.verify_code(request.phone_number, request.verification_code)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="인증 코드가 유효하지 않습니다.")
    return {"message": "전화번호가 성공적으로 인증되었습니다."}

@router.post("/generate-weekly-reports")
async def generate_weekly_reports_manually():
    """주간 보고서 생성을 수동으로 트리거합니다.
    """
    await notification_helper.send_weekly_reports()
    return {"message": "주간 보고서 생성이 트리거되었습니다."}

@router.get("/history", response_model=List[schemas.NotificationLog])
def get_notification_history(
    recipient_user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve notification history. Can be filtered by recipient_user_id.
    """
    logs = crud_service.get_notification_logs(
        db=db, recipient_user_id=recipient_user_id, skip=skip, limit=limit
    )
    return logs

@router.get("/reports", response_model=List[schemas.Report])
def get_weekly_reports(
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve weekly reports. Can be filtered by user_id and date range.
    """
    reports = crud_service.get_reports(
        db=db, user_id=user_id, start_date=start_date, end_date=end_date, skip=skip, limit=limit
    )
    return reports