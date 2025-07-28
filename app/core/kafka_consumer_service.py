import logging
from confluent_kafka import Consumer, KafkaException, KafkaError
import json
import threading
import time
import asyncio
from app.config.config import Config # Config 임포트 추가
from app.helper import notification_helper

logger = logging.getLogger(__name__)

KAFKA_BROKER_URL = Config.KAFKA_BROKER_URL # Config에서 직접 가져오도록 수정
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
            await notification_helper.process_score_update_message(message_payload)
        elif topic == 'notification-requests':
            task = message_payload.get('task')
            if task == 'send_weekly_report':
                await notification_helper.send_weekly_reports()
            elif task == 'check_inactive_users':
                await notification_helper.check_activity_and_notify()
            else:
                logger.warning(f"Unknown task in notification-requests topic: {task}")

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
            'bootstrap.servers': Config.KAFKA_BROKER_URL, # Config.KAFKA_BROKER_URL 사용
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