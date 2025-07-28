import httpx
import logging
from typing import List, Dict, Any
from app.config.config import Config

logger = logging.getLogger(__name__)

USER_SERVICE_URL = Config.USER_SERVICE_URL

async def get_senior_users() -> List[Dict[str, Any]]:
    """
    user-service에서 모든 시니어 사용자 목록을 가져옵니다.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{USER_SERVICE_URL}/users/?role=senior")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching senior users: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Request error fetching senior users: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred fetching senior users: {e}")
            return []

async def get_guardians_for_senior(senior_id: int) -> List[Dict[str, Any]]:
    """
    user-service에서 특정 시니어 사용자의 보호자 목록을 가져옵니다.
    보호자가 없는 경우 빈 리스트를 반환합니다.
    """
    async with httpx.AsyncClient() as client:
        try:
            guardian_response = await client.get(f"{USER_SERVICE_URL}/users/{senior_id}/guardians")
            guardian_response.raise_for_status()
            return guardian_response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"No guardians found for senior {senior_id} (404 Not Found).")
                return []
            else:
                logger.error(f"HTTP error fetching guardians for senior {senior_id}: {e.response.status_code} - {e.response.text}")
                return []
        except httpx.RequestError as e:
            logger.error(f"Request error fetching guardians for senior {senior_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred fetching guardians for senior {senior_id}: {e}")
            return []