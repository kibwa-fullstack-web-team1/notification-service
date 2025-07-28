import json
from confluent_kafka import Producer
from app.config.config import Config

config = Config()

producer = Producer({'bootstrap.servers': config.KAFKA_BROKER_URL})

def publish_message(topic, message):
    """
    지정된 토픽으로 메시지를 발행합니다.
    """
    try:
        producer.produce(topic, value=json.dumps(message).encode('utf-8'))
        producer.flush()
        print(f"Message published to topic '{topic}': {message}")
    except Exception as e:
        print(f"Failed to publish message to topic '{topic}': {e}")
