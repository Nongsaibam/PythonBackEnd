from pydantic import BaseModel

class SendOTPRequest(BaseModel):
    username: str
    phone: str

class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str
