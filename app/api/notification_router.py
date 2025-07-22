from fastapi import APIRouter, HTTPException, status
from app.core.aws_notification_service import AWSNotificationService
from app.schemas.notification_schemas import EmailRequest, SmsRequest
from app.schemas.verification_schemas import PhoneNumberRequest, VerificationCodeRequest, VerificationResponse

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

@router.post("/send-email")
async def send_email_notification(request: EmailRequest):
    notification_service = AWSNotificationService()
    success = notification_service.send_email(
        request.sender_email,
        request.recipient_email,
        request.subject,
        request.body
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send email")
    return {"message": "Email sent successfully"}

@router.post("/send-sms")
async def send_sms_notification(request: SmsRequest):
    notification_service = AWSNotificationService()
    success = notification_service.send_sms(
        request.phone_number,
        request.message
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send SMS")
    return {"message": "SMS sent successfully"}
