import asyncio
from datetime import datetime
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.sms import send_sms
from app.models.scheduled_message import ScheduledMessage
from app.models.contact import Contact
from app.models.vin import VIN

async def send_scheduled_messages():
    print("Scheduler: Checking for scheduled messages...")
    async for session in get_session():
        try:
            now = datetime.now()
            # Select messages that are due and pending
            result = await session.execute(
                select(ScheduledMessage).where(
                    ScheduledMessage.scheduled_time <= now,
                    ScheduledMessage.status == "pending"
                )
            )
            messages_to_send = result.scalars().all()

            for msg in messages_to_send:
                # Fetch contact and VIN details for message context
                contact = await session.get(Contact, msg.contact_id)
                vin = await session.get(VIN, msg.vin_id)

                if contact and contact.phone_number:
                    print(f"Scheduler: Sending message to {contact.phone_number} for VIN {vin.vin[-6:]}...")
                    success = await send_sms(contact.phone_number, msg.message_content)
                    if success:
                        msg.status = "sent"
                        msg.sent_at = datetime.now()
                        print(f"Scheduler: Message {msg.id} sent successfully.")
                    else:
                        msg.status = "failed"
                        print(f"Scheduler: Failed to send message {msg.id}.")
                else:
                    msg.status = "failed" # No contact or phone number
                    print(f"Scheduler: Message {msg.id} failed: No valid contact or phone number.")
                
                session.add(msg)
            
            await session.commit()
        except Exception as e:
            print(f"Scheduler Error: {e}")
        finally:
            await session.close()

async def start_scheduler():
    while True:
        await send_scheduled_messages()
        await asyncio.sleep(60) # Check every 60 seconds
