import boto3
from botocore.exceptions import ClientError
from app.config.config import Config

ses_client = boto3.client(
    "ses",
    region_name=Config.AWS_REGION,
    aws_access_key_id=Config.AWS_SES_SNS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SES_SNS_SECRET_ACCESS_KEY
)

sns_client = boto3.client(
    "sns",
    region_name=Config.AWS_REGION,
    aws_access_key_id=Config.AWS_SES_SNS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SES_SNS_SECRET_ACCESS_KEY
)

def send_email(sender_email: str, recipient_email: str, subject: str, body: str) -> bool:
    try:
        response = ses_client.send_email(
            Source=sender_email,
            Destination={'ToAddresses': [recipient_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
        print(f"이메일 발송 성공! 메시지 ID: {response['MessageId']}")
        return True
    except ClientError as e:
        print(f"이메일 발송 오류: {e.response['Error']['Message']}")
        return False

def send_sms(phone_number: str, message: str) -> bool:
    try:
        response = sns_client.publish(
            PhoneNumber=phone_number,
            Message=message
        )
        print(f"SMS 발송 성공! 메시지 ID: {response['MessageId']}")
        return True
    except ClientError as e:
        print(f"SMS 발송 오류: {e.response['Error']['Message']}")
        return False

def send_verification_sms(phone_number: str, code: str) -> bool:
    message = f"[KIBWA] 인증번호는 [{code}] 입니다."
    return send_sms(phone_number, message)
