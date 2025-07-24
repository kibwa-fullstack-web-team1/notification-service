import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AWS_REGION = os.getenv("AWS_REGION")
    AWS_SES_SNS_ACCESS_KEY_ID = os.getenv("AWS_SES_SNS_ACCESS_KEY_ID")
    AWS_SES_SNS_SECRET_ACCESS_KEY = os.getenv("AWS_SES_SNS_SECRET_ACCESS_KEY")
    KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL") 
    DAILY_QUESTION_SERVICE_URL = os.getenv("DAILY_QUESTION_SERVICE_URL", "http://daily-question-service:8001")
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")