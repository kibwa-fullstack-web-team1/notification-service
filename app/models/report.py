from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.utils.db import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    report_url = Column(String, nullable=False)
    s3_object_name = Column(String, nullable=False)
    report_date = Column(DateTime(timezone=True), default=func.now(), server_default=func.now())
