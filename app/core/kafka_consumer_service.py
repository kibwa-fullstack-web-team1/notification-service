import logging
from confluent_kafka import Consumer, KafkaException, KafkaError
import json
import threading
import time
import httpx
import asyncio
from app.config.config import Config

logger = logging.getLogger(__name__)

KAFKA_BROKER_URL = Config.KAFKA_BROKER_URL
DAILY_QUESTION_SERVICE_URL = Config.DAILY_QUESTION_SERVICE_URL
USER_SERVICE_URL = Config.USER_SERVICE_URL

_consumer_instance = None
_consumer_thread = None
_consumer_running_flag = [False]

async def _process_message(msg):
    logger.info(f"Attempting to process message from topic: {msg.topic()}")
    try:
        message_payload = json.loads(msg.value().decode('utf-8'))
        topic = msg.topic()

        if topic == 'score-updates':
            user_id = message_payload.get('user_id')
            cognitive_score = message_payload.get('cognitive_score')
            semantic_score = message_payload.get('semantic_score')
            timestamp = message_payload.get('timestamp')

            logger.info(f"Received message: {msg.value().decode('utf-8')} from topic {msg.topic()}")
            logger.info(f"Processing score update for user {user_id}: Cognitive={cognitive_score}, Semantic={semantic_score}")

            async def send_notification_to_guardian_async():
                logger.info(f"Inside send_notification_to_guardian_async for user {user_id}")
                async with httpx.AsyncClient() as client:
                    try:
                        logger.info(f"Calling user service for guardians of user {user_id} at {USER_SERVICE_URL}/users/{user_id}/guardians")
                        guardian_response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}/guardians")
                        guardian_response.raise_for_status()
                        guardians = guardian_response.json()
                        logger.info(f"Received guardians: {guardians}")

                        for guardian in guardians:
                            guardian_email = guardian.get('email')
                            guardian_phone = guardian.get('phone_number')
                            notification_message = f"어머님의 최신 인지 건강 점수는 {cognitive_score}점, 맥락 점수는 {semantic_score}점입니다."
                            logger.info(f"Sending notification to guardian {guardian_email}/{guardian_phone}: {notification_message}")

                    except httpx.HTTPStatusError as e:
                        logger.error(f"보호자 정보 조회 HTTP 오류: {e.response.status_code} - {e.response.text}")
                    except httpx.RequestError as e:
                        logger.error(f"보호자 서비스 연결 오류: {e}")
                    except Exception as e:
                        logger.error(f"알림 발송 중 오류: {e}")

            await send_notification_to_guardian_async()

    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from message: {msg.value().decode('utf-8')}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")

async def _run_consumer_loop(consumer, topics, running_flag):
    logger.debug("DEBUG: _run_consumer_loop entered")
    try:
        consumer.subscribe(topics)
        logger.info("Kafka consumer subscribed to topics.")

        while running_flag[0]:
            logger.debug("Kafka consumer polling for messages...")
            msg = consumer.poll(timeout=10.0)
            if msg is None:
                logger.debug("No message received within timeout. Continuing to poll...")
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.debug(f"%% {msg.topic()} [{msg.partition()}] reached end offset {msg.offset()}")
                elif msg.error():
                    logger.error(f"Kafka consumer error: {msg.error()}")
                    raise KafkaException(msg.error())
            else:
                await _process_message(msg)

    except Exception as e:
        logger.exception(f"Kafka consumer loop encountered an error: {e}")
    finally:
        consumer.close()
        logger.info("Consumer closed.")

def start_kafka_consumer(topics):
    logger.debug("DEBUG: start_kafka_consumer called")
    global _consumer_instance, _consumer_thread, _consumer_running_flag

    if not _consumer_running_flag[0]:
        _consumer_instance = Consumer({
            'bootstrap.servers': KAFKA_BROKER_URL,
            'group.id': 'notification_group_v2',
            'auto.offset.reset': 'earliest',
            'debug': 'consumer,broker,topic' # Kafka C library 디버그 로깅 활성화
        })
        _consumer_running_flag[0] = True
        _consumer_thread = threading.Thread(target=lambda: asyncio.run(_run_consumer_loop(_consumer_instance, topics, _consumer_running_flag)))
        _consumer_thread.daemon = True
        _consumer_thread.start()
        logger.info(f"Kafka consumer started for topics: {topics}")

def stop_kafka_consumer():
    global _consumer_running_flag, _consumer_thread, _consumer_instance
    if _consumer_running_flag[0]:
        _consumer_running_flag[0] = False
        if _consumer_thread:
            _consumer_thread.join()
        if _consumer_instance:
            _consumer_instance.close()
        logger.info("Consumer closed.")