from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from app.models.service_record import ServiceRecord
from app.schemas.service_record.create_service_record import ServiceRecordCreate
from app.models.vin import VIN
from app.core.database import get_session

router = APIRouter()

@router.post("/")
def add_service_record(record_in: ServiceRecordCreate, session: Session = Depends(get_session)):
    # Check if VIN exists
    vin = session.exec(select(VIN).where(VIN.id == record_in.vin_id)).first()
    if not vin:
        raise HTTPException(status_code=404, detail="VIN not found")

    # Create ServiceRecord instance from validated schema
    record = ServiceRecord.from_orm(record_in)
    session.add(record)
    session.commit()
    session.refresh(record)

    # Here you can add logic to generate the pickup text, queue reminder, etc.
    # For now, just return the created record
    return record
