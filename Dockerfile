FROM python:3.12-slim

WORKDIR /app

# 필요한 시스템 의존성 설치 (curl 추가)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사 및 설치
COPY notification-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY notification-service/app ./app
COPY notification-service/notification-service_manage.py .

# 스크립트에 실행 권한 부여
RUN chmod +x notification-service_manage.py

# 서비스 포트 노출
EXPOSE 8002

# 애플리케이션 실행 명령어
ENTRYPOINT ["python", "notification-service_manage.py"]