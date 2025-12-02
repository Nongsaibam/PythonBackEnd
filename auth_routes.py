from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import SessionLocal
from models import User, OTP
from schemas import SendOTPRequest, VerifyOTPRequest
from datetime import datetime, timedelta
import random, jwt, os
from twilio.rest import Client

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET")

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# SEND OTP

@router.post("/send-otp")
def send_otp(body: SendOTPRequest, db: Session = Depends(get_db)):
    otp_value = str(random.randint(100000, 999999))
    expires = datetime.utcnow() + timedelta(minutes=5)

    # Save OTP
    new_otp = OTP(phone=body.phone, otp=otp_value, expires_at=expires)
    db.add(new_otp)

    # Create or update user
    user = db.query(User).filter(User.phone == body.phone).first()
    if not user:
        user = User(username=body.username, phone=body.phone)
        db.add(user)

    db.commit()

    # SEND OTP USING TWILIO 
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        client.messages.create(
            body=f"Your OTP is: {otp_value}",
            from_=TWILIO_FROM,
            to=body.phone
        )
    except Exception as e:
        print("Twilio Error:", e)
        raise HTTPException(500, "Failed to send OTP. Check Twilio credentials.")
 

    return {"message": "OTP sent successfully"}



# VERIFY OTP

@router.post("/verify-otp")
def verify_otp(body: VerifyOTPRequest, db: Session = Depends(get_db)):
    otp_record = (
        db.query(OTP)
        .filter(OTP.phone == body.phone, OTP.verified == False)
        .order_by(OTP.id.desc())
        .first()
    )

    if not otp_record:
        raise HTTPException(400, "OTP not found")

    if otp_record.expires_at < datetime.utcnow():
        raise HTTPException(400, "OTP expired")

    if otp_record.otp != body.otp:
        raise HTTPException(400, "Invalid OTP")

    otp_record.verified = True
    db.commit()

    # Get user
    user = db.query(User).filter(User.phone == body.phone).first()

    # Generate JWT
    token = jwt.encode(
        {
            "user_id": user.id,
            "phone": user.phone,
            "exp": datetime.utcnow() + timedelta(days=7)
        },
        JWT_SECRET,
        algorithm="HS256"
    )

    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "phone": user.phone
        }
    }



# CURRENT USER

@router.get("/me")
def me(token: str):
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {"user": data}
    except:
        raise HTTPException(401, "Invalid or expired token")
