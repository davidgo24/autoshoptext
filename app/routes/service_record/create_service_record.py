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

    # Cancel any pending reminders for this VIN to avoid outdated messages
    pending_q = await session.execute(
        select(ScheduledMessage).where(
            ScheduledMessage.vin_id == vin.id,
            ScheduledMessage.status == "pending"
        )
    )
    for msg in pending_q.scalars().all():
        msg.status = "canceled"
        session.add(msg)
    await session.commit()

    return record
