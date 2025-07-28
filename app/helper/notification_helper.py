import asyncio
import logging
import httpx
import datetime
from datetime import timedelta
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
                relationship_display_name = guardian.get('relationship_display_name', '보호자') # 관계 표시명 가져오기
                notification_message = f"[기억의 정원] {relationship_display_name}님의 최근 활동에 주의가 필요하여 알려드립니다. 사유: {notification_reason}"
                
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

async def send_weekly_reports():
    logger.info("Starting weekly report generation...")
    async with httpx.AsyncClient() as client:
        try:
            # 1. 모든 시니어 사용자 정보 가져오기
            response = await client.get(f"{USER_SERVICE_URL}/users/?role=senior")
            response.raise_for_status()
            seniors = response.json()

            for senior in seniors:
                senior_id = senior.get('id')
                # 2. 각 시니어의 주간 답변 데이터 가져오기 (지난 7일)
                start_date = (datetime.datetime.now() - timedelta(days=7)).isoformat()
                end_date = datetime.datetime.now().isoformat()
                answers_response = await client.get(
                    f"{Config.DAILY_QUESTION_SERVICE_URL}/questions/answers?user_id={senior_id}&start_date={start_date}&end_date={end_date}"
                )
                if answers_response.status_code != 200:
                    logger.warning(f"Could not fetch answers for user {senior_id}")
                    continue
                
                answers = answers_response.json()
                logger.info(f"Answers for user {senior_id}: {answers}") # 추가

                # 3. HTML 보고서 생성
                report_html = "<h1>주간 보고서</h1>"
                report_html += f"<h2>{senior.get('username')}님</h2>"
                report_html += "<table border='1'><tr><th>질문</th><th>답변</th><th>분석 점수</th></tr>"
                for answer in answers:
                    report_html += f"<tr><td>{answer.get('question_content')}</td><td>{answer.get('text_content')}</td><td>인지점수: {answer.get('cognitive_score')}, 의미점수: {answer.get('semantic_score')}</td></tr>"
                report_html += "</table>"

                # 4. 보고서 S3에 업로드
                today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                object_name = f"reports/{senior_id}/{today_str}.html"
                logger.info(f"Report HTML type: {type(report_html)}, content length: {len(report_html) if report_html else 0}") # 추가
                report_url = aws_notification_service.upload_file_to_s3(
                    file_content=report_html,
                    bucket_name=Config.AWS_S3_BUCKET_NAME,
                    object_name=object_name
                )

                if report_url is None:
                    logger.error(f"Failed to upload report for user {senior_id}: S3 upload returned None")
                    continue

                # 5. 보호자에게 이메일 발송
                guardians = []
                try:
                    guardian_response = await client.get(f"{USER_SERVICE_URL}/users/{senior_id}/guardians")
                    guardian_response.raise_for_status() # 2xx 응답이 아니면 예외 발생
                    guardians = guardian_response.json()
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        logger.info(f"No guardians found for senior {senior_id} (404 Not Found). Skipping report delivery.")
                        continue # 보호자가 없으면 다음 시니어로 넘어감
                    else:
                        logger.error(f"HTTP error fetching guardians for senior {senior_id}: {e.response.status_code} - {e.response.text}")
                        continue
                except httpx.RequestError as e:
                    logger.error(f"Request error fetching guardians for senior {senior_id}: {e}")
                    continue

                if not guardians:
                    logger.info(f"No guardians found for senior {senior_id}. Skipping report delivery.")
                    continue

                for guardian in guardians:
                    if report_url: # report_url이 None이 아닐 때만 이메일 발송
                        aws_notification_service.send_email(
                            sender_email="kibwateam1@gmail.com",
                            recipient_email=guardian.get('email'),
                            subject=f"[{senior.get('username')}]님의 주간 기억의 정원 보고서",
                            body=f'<p><a href="{report_url}">여기</a>를 클릭하여 주간 보고서를 확인하세요.</p>'
                        )

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during weekly report generation: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"An error occurred during weekly report generation: {e}")

async def check_activity_and_notify():
    logger.info("'check_activity_and_notify' task received and will be processed.")
    # 여기에 실제 활동 이상 징후 감지 및 알림 로직 추가 예정
    await asyncio.sleep(5) # 임시로 5초 대기
    logger.info("Activity check completed.")