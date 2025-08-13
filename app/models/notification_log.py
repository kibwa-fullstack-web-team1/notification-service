from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.utils.db import Base

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    triggering_user_id = Column(Integer, nullable=False, index=True)
    recipient_user_id = Column(Integer, nullable=False, index=True)
    message = Column(Text, nullable=False)
    status = Column(String, nullable=False)
    provider_response = Column(JSONB, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
