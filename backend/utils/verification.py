import random
import string
import hashlib
from fastapi import HTTPException
from database.connection import settings
import logging



# Twilio SDK
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

# Generate a 6-digit OTP
def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))

def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def send_phone_otp(phone_number: str, otp: str) -> bool:
    """Uses Twilio Programmable SMS API to send SMS OTP"""
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    twilio_phone = settings.TWILIO_PHONE_NUMBER
    
    if not account_sid or not auth_token or not twilio_phone:
        # Fallback for local development if not configured
        logger.warning(f"DEV MODE: Phone OTP for {phone_number} is {otp}")
        return True
        
    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=f"Your TERRAVYN verification code is {otp}. It expires in 10 minutes.",
            from_=twilio_phone,
            to=phone_number
        )
        return True
    except TwilioRestException as e:
        logger.error(f"Twilio Rest Error: {e.msg}")
        raise HTTPException(status_code=500, detail="Unable to send verification SMS. Please try again later.")
    except Exception as e:
        logger.error(f"Twilio Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Unable to send verification SMS. Please try again later.")
