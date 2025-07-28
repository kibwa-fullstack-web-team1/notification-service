from fastapi import FastAPI
from app.api.notification_router import router as notification_router
from app.core.kafka_consumer_service import start_kafka_consumer, stop_kafka_consumer
from app.core.scheduler_service import start_scheduler, stop_scheduler
import asyncio
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import KafkaException
from app.config.config import Config
from app.utils.logger import setup_logging
import logging

from app.utils.db import Base, engine
from app.models import report # Report 모델 임포트

logger = logging.getLogger(__name__)

def create_app():
    setup_logging() # 로깅 설정 초기화
    app = FastAPI()

    app.include_router(notification_router)

    @app.on_event("startup")
    async def startup_event():
        logger.info("Application startup event triggered.")
        
        # DB 테이블 생성
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/checked.")
        
        # Kafka 브로커 준비 대기 및 토픽 생성 로직
        admin_client = AdminClient({'bootstrap.servers': Config.KAFKA_BROKER_URL})
        max_retries = 60
        retry_delay = 2
        
        for i in range(max_retries):
            try:
                metadata = admin_client.list_topics(timeout=1)
                logger.info(f"Kafka brokers are ready: {metadata.brokers}")

                topics_to_create = ['score-updates', 'notification-requests']
                existing_topics = metadata.topics
                new_topics = []
                for topic_name in topics_to_create:
                    if topic_name not in existing_topics:
                        logger.info(f"Topic '{topic_name}' not found. Creating it...")
                        new_topics.append(NewTopic(topic_name, num_partitions=1, replication_factor=1))
                    else:
                        logger.info(f"Topic '{topic_name}' already exists.")
                
                if new_topics:
                    admin_client.create_topics(new_topics)
                    logger.info(f"Topics created successfully.")

                break
            except KafkaException as e:
                logger.warning(f"Waiting for Kafka brokers to be ready... ({i+1}/{max_retries}) - {e}")
                await asyncio.sleep(retry_delay)
            except Exception as e:
                logger.error(f"An unexpected error occurred while waiting for Kafka: {e}")
                await asyncio.sleep(retry_delay)
        else:
            logger.error("Failed to connect to Kafka brokers after multiple retries. Consumer and scheduler will not start.")
            return

        start_kafka_consumer(topics=['score-updates', 'notification-requests']) # Kafka 컨슈머 시작
        start_scheduler() # 스케줄러 시작
        await asyncio.sleep(5) # 컨슈머 및 스케줄러 시작 대기

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Application shutdown event triggered.")
        stop_kafka_consumer()
        stop_scheduler()

    @app.get("/")
    async def root():
        return {"message": "Notification Service is running"}

    return app
