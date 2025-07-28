import httpx
from app.config.config import Config
import logging

logger = logging.getLogger(__name__)

DAILY_QUESTION_SERVICE_URL = Config.DAILY_QUESTION_SERVICE_URL

async def get_answers_by_user(user_id: int, start_date: str, end_date: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{DAILY_QUESTION_SERVICE_URL}/questions/answers?user_id={user_id}&start_date={start_date}&end_date={end_date}"
            )
            response.raise_for_status()
            answers_data = response.json()
            logger.info(f"Received answers data from daily-question-service: {answers_data}")
            return answers_data
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching answers for user {user_id}: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching answers for user {user_id}: {e}")
            return None
