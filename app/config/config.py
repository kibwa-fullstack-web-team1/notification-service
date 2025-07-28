import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AWS_REGION = os.getenv("AWS_REGION")
    AWS_SES_SNS_ACCESS_KEY_ID = os.getenv("AWS_SES_SNS_ACCESS_KEY_ID")
    AWS_SES_SNS_SECRET_ACCESS_KEY = os.getenv("AWS_SES_SNS_SECRET_ACCESS_KEY")
    AWS_S3_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_S3_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL") 
    DAILY_QUESTION_SERVICE_URL = os.getenv("DAILY_QUESTION_SERVICE_URL", "http://daily-question-service:8001")
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
    DATABASE_URL = os.getenv("DATABASE_URL")

    # 알림 발송을 위한 점수 임계값
    # 70점: 인지적으로 건강한 상태를 구분하는 기준선 (점수산정방식.md 참고)
    # 50점: 답변의 의미 유사도가 '보통' 수준인지를 판단하는 기술적 기준 (연구결과.md, KT1-123 참고)
    COGNITIVE_SCORE_THRESHOLD = int(os.getenv("COGNITIVE_SCORE_THRESHOLD", "70"))
    SEMANTIC_SCORE_THRESHOLD = int(os.getenv("SEMANTIC_SCORE_THRESHOLD", "50"))