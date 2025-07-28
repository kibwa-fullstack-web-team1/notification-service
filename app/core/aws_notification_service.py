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

s3_client = boto3.client(
    "s3",
    region_name=Config.AWS_REGION,
    aws_access_key_id=Config.AWS_S3_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_S3_SECRET_ACCESS_KEY
)

print(f"S3 Client Config: Region={Config.AWS_REGION}, AccessKeyId={Config.AWS_S3_ACCESS_KEY_ID}, SecretAccessKey={'*' * len(Config.AWS_S3_SECRET_ACCESS_KEY) if Config.AWS_S3_SECRET_ACCESS_KEY else 'None'}")
print(f"AWS_REGION: {Config.AWS_REGION}")
print(f"AWS_S3_ACCESS_KEY_ID: {Config.AWS_S3_ACCESS_KEY_ID}")
print(f"AWS_S3_SECRET_ACCESS_KEY: {'*' * len(Config.AWS_S3_SECRET_ACCESS_KEY) if Config.AWS_S3_SECRET_ACCESS_KEY else 'None'}")

def upload_file_to_s3(file_content: str, bucket_name: str, object_name: str) -> str:
    """
    파일 내용을 S3에 업로드하고 URL을 반환합니다.
    """
    try:
        print("S3 업로드 시도 중...")
        print(f"file_content type: {type(file_content)}, value: {file_content[:100]}...") # 추가
        s3_client.put_object(Body=file_content.encode('utf-8'), Bucket=bucket_name, Key=object_name, ContentType='text/html')
        url = f"https://{bucket_name}.s3.{Config.AWS_REGION}.amazonaws.com/{object_name}"
        print(f"S3 업로드 성공! URL: {url}")
        print("S3 업로드 함수 종료 (성공)")
        return url
    except ClientError as e:
        print(f"S3 업로드 오류: {e}")
        print(f"S3 업로드 오류 상세: {e.response}")
        print("S3 업로드 함수 종료 (오류)")
        return None
    except Exception as e:
        print(f"예상치 못한 S3 업로드 오류: {e}")
        print("S3 업로드 함수 종료 (예상치 못한 오류)")
        return None

def send_email(sender_email: str, recipient_email: str, subject: str, body: str) -> bool:
    try:
        response = ses_client.send_email(
            Source=sender_email,
            Destination={'ToAddresses': [recipient_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Html': {'Data': body}}
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
    message = f"[GARDEN-OF-MEMORIES] 인증번호는 [{code}] 입니다."
    return send_sms(phone_number, message)
