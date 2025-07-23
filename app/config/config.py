import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AWS_REGION = os.getenv("AWS_REGION")
    AWS_SES_SNS_ACCESS_KEY_ID = os.getenv("AWS_SES_SNS_ACCESS_KEY_ID")
    AWS_SES_SNS_SECRET_ACCESS_KEY = os.getenv("AWS_SES_SNS_SECRET_ACCESS_KEY")
