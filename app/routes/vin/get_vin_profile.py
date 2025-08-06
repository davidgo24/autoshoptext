from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.models.vin import VIN
from app.core.database import get_session

router = APIRouter()

@router.get("/{vin_or_last8}")
def get_vin_profile(vin_or_last8: str, session: Session = Depends(get_session)):
    # Support searching full VIN or last 8 characters
    if len(vin_or_last8) == 17:
        query = select(VIN).where(VIN.vin == vin_or_last8)
    else:
        # Search by last 8 characters (case insensitive)
        query = select(VIN).where(VIN.vin.endswith(vin_or_last8.upper()))

    vin = session.exec(query.options(selectinload(VIN.service_records))).first()
    if not vin:
        raise HTTPException(status_code=404, detail="VIN not found")

    return vin
