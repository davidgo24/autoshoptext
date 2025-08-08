from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.vin import VIN
from app.models.vin_contact_link import VINContactLink
from app.core.database import get_session
from app.schemas.service_record.read_service_record import ServiceRecordRead
from app.schemas.contact.contact import Contact
from app.schemas.vin.read_vin_profile import VinProfileRead

router = APIRouter()

@router.get("/{vin_or_last8}", response_model=VinProfileRead)
async def get_vin_profile(
    vin_or_last8: str,
    session: AsyncSession = Depends(get_session),
):
    # Compose query based on VIN length
    if len(vin_or_last8) == 17:
        query = select(VIN).where(VIN.vin == vin_or_last8)
    else:
        query = select(VIN).where(VIN.vin.endswith(vin_or_last8.upper()))

    # Use options to eager load related service_records
    query = query.options(joinedload(VIN.service_records), joinedload(VIN.contact_links).joinedload(VINContactLink.contact))

    # Execute asynchronously
    result = await session.execute(query)
    vin = result.scalars().first()

    if not vin:
        raise HTTPException(status_code=404, detail="VIN not found")

    # Manually construct VinProfileRead to include contacts and service records as their Read schemas
    vin_profile_read = VinProfileRead(
        id=vin.id,
        vin=vin.vin,
        make=vin.make,
        model=vin.model,
        year=vin.year,
        trim=vin.trim,
        plate=vin.plate,
        service_records=[ServiceRecordRead.from_orm(sr) for sr in vin.service_records], # Convert to ServiceRecordRead
        contacts=[Contact.from_orm(link.contact) for link in vin.contact_links if link.contact] # Convert to ContactRead
    )

    return vin_profile_read
