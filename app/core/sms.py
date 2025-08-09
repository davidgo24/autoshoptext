import os
import re
import time
from collections import defaultdict
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

client = None

if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Rate limiting: Track messages sent per phone number
message_history = defaultdict(list)
MAX_MESSAGES_PER_HOUR = 10  # Per phone number
MAX_MESSAGE_LENGTH = 4800  # Supports up to 3 SMS segments (160 chars × 3 × 10 for safety)

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format"""
    # Remove all non-digits
    digits_only = re.sub(r'\D', '', phone)
    # Must be 10 or 11 digits (US format)
    return len(digits_only) in [10, 11] and digits_only.isdigit()

def check_rate_limit(phone: str) -> bool:
    """Check if phone number has exceeded rate limits"""
    now = time.time()
    hour_ago = now - 3600  # 1 hour ago
    
    # Clean old entries
    message_history[phone] = [timestamp for timestamp in message_history[phone] if timestamp > hour_ago]
    
    # Check if under limit
    return len(message_history[phone]) < MAX_MESSAGES_PER_HOUR

def record_message_sent(phone: str):
    """Record that a message was sent to this phone number"""
    message_history[phone].append(time.time())

async def send_sms(to_phone_number: str, message_body: str):
    """
    Send SMS with safety checks and rate limiting
    """
    if not client:
        print("Twilio client not initialized. SMS will not be sent.")
        return False

    if not TWILIO_PHONE_NUMBER:
        print("TWILIO_PHONE_NUMBER not set. SMS will not be sent.")
        return False

    # Validate phone number
    if not validate_phone_number(to_phone_number):
        print(f"Invalid phone number format: {to_phone_number}")
        return False

    # Check message length
    if len(message_body) > MAX_MESSAGE_LENGTH:
        print(f"Message too long ({len(message_body)} chars). Max: {MAX_MESSAGE_LENGTH}")
        return False

    # Check rate limiting
    if not check_rate_limit(to_phone_number):
        print(f"Rate limit exceeded for {to_phone_number} (max {MAX_MESSAGES_PER_HOUR}/hour)")
        return False

    # Normalize phone number (ensure it starts with +1 for US numbers)
    normalized_phone = to_phone_number
    if not normalized_phone.startswith('+'):
        digits_only = re.sub(r'\D', '', normalized_phone)
        if len(digits_only) == 10:
            normalized_phone = f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            normalized_phone = f"+{digits_only}"
        else:
            normalized_phone = f"+1{digits_only}"

    try:
        message = client.messages.create(
            to=normalized_phone,
            from_=TWILIO_PHONE_NUMBER,
            body=message_body
        )
        print(f"SMS sent to {normalized_phone}: {message.sid}")
        record_message_sent(to_phone_number)  # Record for rate limiting
        return message.sid
    except Exception as e:
        print(f"Error sending SMS to {normalized_phone}: {e}")
        return None
