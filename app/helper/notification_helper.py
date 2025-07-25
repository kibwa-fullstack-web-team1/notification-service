import logging
import httpx
from app.config.config import Config
from app.core import aws_notification_service

logger = logging.getLogger(__name__)

USER_SERVICE_URL = Config.USER_SERVICE_URL

async def send_alert_to_guardians(user_id: int, reasons: list):
    logger.info(f"Inside send_alert_to_guardians for user {user_id}")
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
                
                # SMS 발송
                if guardian_phone:
                    # AWS SNS는 E.164 형식의 전화번호를 선호합니다. (예: +821012345678)
                    # 필요시 전화번호 형식 변환 로직 추가
                    if not guardian_phone.startswith('+'):
                        # 예시: 한국 전화번호 010-1234-5678 -> +821012345678
                        guardian_phone = "+82" + guardian_phone[1:] 
                    aws_notification_service.send_sms(
                        phone_number=guardian_phone,
                        message=notification_message
                    )
                    logger.info(f"SMS 알림 발송 시도: {guardian_phone}")

        except httpx.HTTPStatusError as e:
            logger.error(f"보호자 정보 조회 HTTP 오류: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"보호자 서비스 연결 오류: {e}")
        except Exception as e:
            logger.error(f"알림 발송 중 오류: {e}")

async def process_score_update_message(message_payload: dict):
    user_id = message_payload.get('user_id')
    cognitive_score = message_payload.get('cognitive_score')
    semantic_score = message_payload.get('semantic_score')
    timestamp = message_payload.get('timestamp')

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
        await send_alert_to_guardians(user_id, reasons)
    else:
        logger.info(f"점수가 기준치 이상이므로 알림을 발송하지 않습니다. (인지: {cognitive_score}>={Config.COGNITIVE_SCORE_THRESHOLD}, 의미: {semantic_score}>={Config.SEMANTIC_SCORE_THRESHOLD})")
