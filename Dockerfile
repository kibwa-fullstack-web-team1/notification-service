FROM python:3.12-slim

WORKDIR /app

COPY notification-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY notification-service/app ./app
COPY notification-service/notification-service_manage.py .

CMD ["python", "notification-service_manage.py"]