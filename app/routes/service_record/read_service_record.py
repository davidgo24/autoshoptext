from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.models.service_record import ServiceRecord
from app.models.vin import VIN
from app.models.contact import Contact
from app.models.vin_contact_link import VINContactLink
from app.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/{service_record_id}")
async def get_service_record(service_record_id: int, session: AsyncSession = Depends(get_session)):
    """
    Fetches a single service record by its ID, including the full VIN object
    and all associated contacts.
    """
    result = await session.execute(
        select(ServiceRecord)
        .where(ServiceRecord.id == service_record_id)
        .options(
            selectinload(ServiceRecord.vin).options(
                selectinload(VIN.contact_links).options(
                    selectinload(VINContactLink.contact)
                )
            )
        )
    )
    service_record = result.scalars().first()

    if not service_record:
        raise HTTPException(status_code=404, detail="Service Record not found")

    return service_record
