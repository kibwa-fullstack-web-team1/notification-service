from pydantic import BaseModel

class EmailRequest(BaseModel):
    sender_email: str
    recipient_email: str
    subject: str
    body: str

class SmsRequest(BaseModel):
    phone_number: str
    message: str
