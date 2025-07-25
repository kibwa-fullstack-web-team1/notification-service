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

            # 지능형 알림 조건 확인
            send_notification = False
            reasons = []
            if cognitive_score < Config.COGNITIVE_SCORE_THRESHOLD:
                send_notification = True
                reasons.append(f"인지 점수({cognitive_score})가 기준({Config.COGNITIVE_SCORE_THRESHOLD})보다 낮습니다.")
            if semantic_score < Config.SEMANTIC_SCORE_THRESHOLD:
                send_notification = True
                reasons.append(f"의미 유사도 점수({semantic_score})가 기준({Config.SEMANTIC_SCORE_THRESHOLD})보다 낮습니다.")

            if send_notification:
                async def send_notification_to_guardian_async():
                    logger.info(f"Inside send_notification_to_guardian_async for user {user_id}")
                    async with httpx.AsyncClient() as client:
                        try:
                            logger.info(f"Calling user service for guardians of user {user_id} at {USER_SERVICE_URL}/users/{user_id}/guardians")
                            guardian_response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}/guardians")
                            guardian_response.raise_for_status()
                            guardians = guardian_response.json()
                            logger.info(f"Received guardians: {guardians}")

                            notification_reason = " ".join(reasons)
                            for guardian in guardians:
                                guardian_email = guardian.get('email')
                                guardian_phone = guardian.get('phone_number')
                                notification_message = f"[기억의 정원] 어머님의 최근 활동에 주의가 필요하여 알려드립니다. 사유: {notification_reason}"
                                logger.info(f"Sending notification to guardian {guardian_email}/{guardian_phone}: {notification_message}")

                        except httpx.HTTPStatusError as e:
                            logger.error(f"보호자 정보 조회 HTTP 오류: {e.response.status_code} - {e.response.text}")
                        except httpx.RequestError as e:
                            logger.error(f"보호자 서비스 연결 오류: {e}")
                        except Exception as e:
                            logger.error(f"알림 발송 중 오류: {e}")

                await send_notification_to_guardian_async()
            else:
                logger.info(f"점수가 기준치 이상이므로 알림을 발송하지 않습니다. (인지: {cognitive_score}>={Config.COGNITIVE_SCORE_THRESHOLD}, 의미: {semantic_score}>={Config.SEMANTIC_SCORE_THRESHOLD})")

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
            'auto.offset.reset': 'earliest'
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