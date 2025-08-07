from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from app.models.service_record import ServiceRecord
from app.schemas.service_record.create_service_record import ServiceRecordCreate
from app.models.vin import VIN
from app.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()

@router.post("/")
async def add_service_record(record_in: ServiceRecordCreate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(VIN).where(VIN.vin == record_in.vin))
    vin = result.scalars().first()
    if not vin:
        raise HTTPException(status_code=404, detail="VIN not found")

    # Create a new ServiceRecord instance, but don't include the VIN string itself
    record_data = record_in.dict()
    record_data.pop("vin")
    record = ServiceRecord(**record_data, vin_id=vin.id)
    
    session.add(record)
    await session.commit()
    await session.refresh(record)

    return record
