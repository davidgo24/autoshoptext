from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.models.vin_contact_link import VINContactLink
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import selectinload
from app.models.service_record import ServiceRecord
from app.schemas.service_record.create_service_record import ServiceRecordCreate
from app.models.vin import VIN
from app.models.contact import Contact
from app.models.scheduled_message import ScheduledMessage
from app.models.vin_contact_link import VINContactLink
from app.models.vin_contact_link import VINContactLink
from app.core.database import get_session
from app.core.sms import send_sms
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta


router = APIRouter()

@router.post("/")
async def add_service_record(record_in: ServiceRecordCreate, session: AsyncSession = Depends(get_session)):
    # Fetch VIN with its contacts eagerly loaded
    result = await session.execute(
        select(VIN).where(VIN.vin == record_in.vin).options(selectinload(VIN.contact_links).selectinload(VINContactLink.contact))
    )
    vin = result.scalars().first()
    if not vin:
        raise HTTPException(status_code=404, detail="VIN not found")

    # Create a new ServiceRecord instance
    record_data = record_in.dict()
    record_data.pop("vin")
    record = ServiceRecord(**record_data, vin_id=vin.id)
    
    session.add(record)
    await session.commit()
    await session.refresh(record)

    # --- SMS Logic ---
    # 1. Send immediate "Ready for Pickup" SMS
    ready_message_body = f"Your {vin.make} {vin.model} ({vin.vin[-6:]}) is ready for pickup!"
    for link in vin.contact_links:
        if link.contact.phone_number:
            await send_sms(link.contact.phone_number, ready_message_body)

    # 2. Schedule "Next Service Due" Reminder SMS
    reminder_message_template = (
        "Reminder: Hi {name}, your {make} {model} ({vin_last_6}) is due for service on {next_date_due} or at {next_mileage_due} miles."
    )
    
    for link in vin.contact_links:
        if link.contact.phone_number:
            # Construct the personalized message
            personalized_reminder_message = reminder_message_template.format(
                name=link.contact.name,
                make=vin.make,
                model=vin.model,
                vin_last_6=vin.vin[-6:],
                next_date_due=record.next_service_date_due.strftime("%Y-%m-%d"),
                next_mileage_due=record.next_service_mileage_due
            )

            # Schedule the message for the next service date
            scheduled_msg = ScheduledMessage(
                contact_id=link.contact.id,
                vin_id=vin.id,
                message_content=personalized_reminder_message,
                scheduled_time=datetime.combine(record.next_service_date_due, datetime.min.time()) # Set to start of the day
            )
            session.add(scheduled_msg)
    
    await session.commit() # Commit scheduled messages

    return record
