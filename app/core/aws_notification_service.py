import os
import boto3
from botocore.exceptions import ClientError

class AWSNotificationService:
    def __init__(self):
        self.aws_region = os.getenv("AWS_REGION")
        self.aws_access_key_id = os.getenv("AWS_SES_SNS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SES_SNS_SECRET_ACCESS_KEY")

        self.ses_client = boto3.client(
            "ses",
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )
        self.sns_client = boto3.client(
            "sns",
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )

    def send_email(self, sender_email: str, recipient_email: str, subject: str, body: str) -> bool:
        try:
            response = self.ses_client.send_email(
                Source=sender_email,
                Destination={'ToAddresses': [recipient_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body}}
                }
            )
            print(f"Email sent! Message ID: {response['MessageId']}")
            return True
        except ClientError as e:
            print(f"Error sending email: {e.response['Error']['Message']}")
            return False

    def send_sms(self, phone_number: str, message: str) -> bool:
        try:
            response = self.sns_client.publish(
                PhoneNumber=phone_number,
                Message=message
            )
            print(f"SMS sent! Message ID: {response['MessageId']}")
            return True
        except ClientError as e:
            print(f"SMS 전송 오류: {e.response['Error']['Message']}")
            return False
