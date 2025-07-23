import random
import string

# In-memory storage for verification codes (replace with Redis in production)
verification_codes = {}

def generate_verification_code(phone_number: str) -> str:
    """Generate a 6-digit verification code and store it."""
    code = ''.join(random.choices(string.digits, k=6))
    verification_codes[phone_number] = code
    print(f"인증번호 생성: {phone_number} -> {code}")
    return code

def verify_code(phone_number: str, code: str) -> bool:
    """Verify the provided code."""
    stored_code = verification_codes.get(phone_number)
    if stored_code and stored_code == code:
        del verification_codes[phone_number]
        print(f"인증 성공: {phone_number}")
        return True
    print(f"인증 실패: {phone_number}")
    return False
