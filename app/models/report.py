from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSONB # JSONB 타입 임포트
from sqlalchemy.sql import func
from app.utils.db import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    report_data = Column(JSONB, nullable=False) # JSONB 타입으로 변경
    report_date = Column(DateTime(timezone=True), default=func.now(), server_default=func.now())
