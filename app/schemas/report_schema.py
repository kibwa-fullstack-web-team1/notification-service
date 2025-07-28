from pydantic import BaseModel, ConfigDict
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from typing import Dict, Any
from datetime import datetime

class ReportBase(BaseModel):
    user_id: int
    report_data: Dict[str, Any] # 보고서 내용을 JSON 형태로 저장

class ReportCreate(ReportBase):
    pass

class Report(ReportBase):
    id: int
    report_date: datetime

    model_config = ConfigDict(from_attributes=True)