from pydantic import BaseModel

class PhoneNumberRequest(BaseModel):
    phone_number: str
    language_code: str = "ko-KR" # Default to Korean

class VerificationCodeRequest(BaseModel):
    phone_number: str
    verification_code: str

class VerificationResponse(BaseModel):
    success: bool
    message: str
