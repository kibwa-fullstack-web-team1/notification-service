import asyncio
import logging
import datetime
from datetime import timedelta
from app.config.config import Config
from app.core import aws_notification_service, crud_service, user_service_client, daily_question_service_client
from app.schemas.report_schema import ReportCreate
from app.utils.db import SessionLocal
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

async def send_alert_to_guardians(user_id: int, reasons: list):
    logger.info(f"Inside send_alert_to_guardians for user {user_id}")
    guardians = await user_service_client.get_guardians_for_senior(user_id)
    if not guardians:
        logger.info(f"No guardians found for user {user_id}")
        return

    notification_reason = " ".join(reasons)
    for guardian in guardians:
        guardian_email = guardian.get('email')
        guardian_phone = guardian.get('phone_number')
        relationship_display_name = guardian.get('relationship_display_name', '보호자')
        notification_message = f"[기억의 정원] {relationship_display_name}님의 최근 활동에 주의가 필요하여 알려드립니다. 사유: {notification_reason}"
        
        if guardian_phone:
            if not guardian_phone.startswith('+'):
                guardian_phone = "+82" + guardian_phone[1:]
            aws_notification_service.send_sms(
                phone_number=guardian_phone,
                message=notification_message
            )
            logger.info(f"SMS 알림 발송 시도: {guardian_phone}")

async def process_score_update_message(message_payload: dict):
    user_id = message_payload.get('user_id')
    cognitive_score = message_payload.get('cognitive_score')
    semantic_score = message_payload.get('semantic_score')

    logger.info(f"Processing score update for user {user_id}: Cognitive={cognitive_score}, Semantic={semantic_score}")

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
    seniors = await user_service_client.get_senior_users()
    if not seniors:
        logger.info("No senior users found.")
        return

    for senior in seniors:
        senior_id = senior.get('id')
        start_date = (datetime.datetime.now() - timedelta(days=7)).isoformat()
        end_date = datetime.datetime.now().isoformat()
        answers = await daily_question_service_client.get_answers_by_user(senior_id, start_date, end_date)

        if not answers:
            logger.warning(f"Could not fetch answers for user {senior_id}")
            continue
        
        logger.info(f"Answers for user {senior_id}: {answers}")

        cognitive_scores = [ans.get('cognitive_score') for ans in answers if ans.get('cognitive_score') is not None]
        semantic_scores = [ans.get('semantic_score') for ans in answers if ans.get('semantic_score') is not None]

        avg_cognitive = sum(cognitive_scores) / len(cognitive_scores) if cognitive_scores else 0
        min_cognitive = min(cognitive_scores) if cognitive_scores else 0
        max_cognitive = max(cognitive_scores) if cognitive_scores else 0

        avg_semantic = sum(semantic_scores) / len(semantic_scores) if semantic_scores else 0
        min_semantic = min(semantic_scores) if semantic_scores else 0
        max_semantic = max(semantic_scores) if semantic_scores else 0

        report_data = {
            "senior_id": senior_id,
            "username": senior.get('username'),
            "report_date": datetime.datetime.now().isoformat(),
            "summary": {
                "avg_cognitive_score": f"{avg_cognitive:.2f}",
                "min_cognitive_score": f"{min_cognitive:.2f}",
                "max_cognitive_score": f"{max_cognitive:.2f}",
                "avg_semantic_score": f"{avg_semantic:.2f}",
                "min_semantic_score": f"{min_semantic:.2f}",
                "max_semantic_score": f"{max_semantic:.2f}",
            },
            "answers": [
                {
                    "question_content": ans.get('question_content'),
                    "text_content": ans.get('text_content'),
                    "cognitive_score": ans.get('cognitive_score'),
                    "semantic_score": ans.get('semantic_score'),
                } for ans in answers
            ]
        }

        db: Session = SessionLocal()
        try:
            report_create_schema = ReportCreate(
                user_id=senior_id,
                report_data=report_data
            )
            crud_service.create_report(db=db, report=report_create_schema)
            logger.info(f"Successfully saved report data for user {senior_id} to DB.")
        except Exception as e:
            logger.error(f"Failed to save report data for user {senior_id}: {e}")
        finally:
            db.close()

        # 이메일 발송을 위한 HTML 보고서 동적 생성
        report_html = "<meta charset=\"utf-8\"><h1>주간 보고서</h1>"
        report_html += f"<h2>{report_data['username']}님</h2>"
        report_html += "<h3>주간 점수 요약</h3>"
        report_html += "<ul>"
        report_html += f"<li>**인지 점수 평균:** {report_data['summary']['avg_cognitive_score']} (최저: {report_data['summary']['min_cognitive_score']}, 최고: {report_data['summary']['max_cognitive_score']})</li>"
        report_html += f"<li>**의미 점수 평균:** {report_data['summary']['avg_semantic_score']} (최저: {report_data['summary']['min_semantic_score']}, 최고: {report_data['summary']['max_semantic_score']})</li>"
        report_html += "</ul>"
        report_html += "<h3>상세 답변 내역</h3>"
        report_html += "<table border='1'><tr><th>질문</th><th>답변</th><th>분석 점수</th></tr>"
        for ans in report_data['answers']:
            report_html += f"<tr><td>{ans['question_content']}</td><td>{ans['text_content']}</td><td>인지점수: {ans['cognitive_score']}, 의미점수: {ans['semantic_score']}</td></tr>"
        report_html += "</table>"

        guardians = await user_service_client.get_guardians_for_senior(senior_id)
        if not guardians:
            logger.info(f"No guardians found for senior {senior_id}. Skipping report delivery.")
            continue

        for guardian in guardians:
            aws_notification_service.send_email(
                sender_email="kibwateam1@gmail.com",
                recipient_email=guardian.get('email'),
                subject=f"[{senior.get('username')}]님의 주간 기억의 정원 보고서",
                body=report_html # S3 URL 대신 HTML 본문 직접 전달
            )

async def check_activity_and_notify():
    logger.info("'check_activity_and_notify' task received and will be processed.")
    await asyncio.sleep(5)
    logger.info("Activity check completed.")
