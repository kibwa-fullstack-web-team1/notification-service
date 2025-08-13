from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

# Base schema with common attributes
class NotificationLogBase(BaseModel):
    triggering_user_id: int
    recipient_user_id: int
    message: str
    status: str

    class Config:
        orm_mode = True

# Schema for creating a new log (used in service layer)
class NotificationLogCreate(NotificationLogBase):
    provider_response: Optional[dict] = None

# Schema for reading a log from the API (includes DB-generated fields)
class NotificationLog(NotificationLogBase):
    id: int
    sent_at: datetime
    provider_response: Optional[Any] = None # Using Any for flexibility with JSONB
