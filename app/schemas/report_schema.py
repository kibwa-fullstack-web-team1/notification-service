from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ReportBase(BaseModel):
    user_id: int
    report_url: str
    s3_object_name: str

class ReportCreate(ReportBase):
    pass

class Report(ReportBase):
    id: int
    report_date: datetime

    model_config = ConfigDict(from_attributes=True)