from pydantic import BaseModel

# Phone Number Verification Schemas
class PhoneNumberRequest(BaseModel):
    phone_number: str
    language_code: str = "ko-KR" # Default to Korean

class VerificationCodeRequest(BaseModel):
    phone_number: str
    verification_code: str

class VerificationResponse(BaseModel):
    success: bool
    message: str

# Email Verification Schemas
class EmailVerificationRequest(BaseModel):
    email: str

class EmailVerificationConfirm(BaseModel):
    email: str
    verification_code: str
