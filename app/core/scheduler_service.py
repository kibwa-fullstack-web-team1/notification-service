from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.kafka_producer_service import publish_message
import datetime

scheduler = AsyncIOScheduler()

def schedule_jobs():
    """
    주기적인 작업을 Kafka 토픽에 메시지로 발행합니다.
    """
    now = datetime.datetime.now().isoformat()
    
    # 주간 보고서 발송 요청
    publish_message('notification-requests', {"task": "send_weekly_report", "timestamp": now})
    
    # 활동 이상 징후 감지 요청
    publish_message('notification-requests', {"task": "check_inactive_users", "timestamp": now})

def start_scheduler():
    """
    스케줄러를 시작하고 주기적인 작업을 등록합니다.
    """
    # 1분마다 작업 발행 (테스트용)
    scheduler.add_job(schedule_jobs, 'interval', weeks=1)
    
    scheduler.start()
    print("Scheduler started and jobs are scheduled.")

def stop_scheduler():
    """
    스케줄러를 종료합니다.
    """
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler stopped...")
