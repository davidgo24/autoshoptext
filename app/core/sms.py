import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

client = None

if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

async def send_sms(to_phone_number: str, message_body: str):
    if not client:
        print("Twilio client not initialized. SMS will not be sent.")
        return

    if not TWILIO_PHONE_NUMBER:
        print("TWILIO_PHONE_NUMBER not set. SMS will not be sent.")
        return

    try:
        message = client.messages.create(
            to=to_phone_number,
            from_=TWILIO_PHONE_NUMBER,
            body=message_body
        )
        print(f"SMS sent to {to_phone_number}: {message.sid}")
        return message.sid
    except Exception as e:
        print(f"Error sending SMS to {to_phone_number}: {e}")
        return None
