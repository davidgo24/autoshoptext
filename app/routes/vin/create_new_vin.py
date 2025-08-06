from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from app.models.vin import VIN
from app.schemas.vin.create_new_vin import VinCreate
from app.core.database import get_session

router = APIRouter()

@router.post("/", response_model=VinCreate)
def create_vin(vin_in: VinCreate, session: Session = Depends(get_session)):
    vin_exists = session.exec(select(VIN).where(VIN.vin == vin_in.vin)).first()
    if vin_exists:
        raise HTTPException(status_code=400, detail="VIN already exists")

    vin = VIN.from_orm(vin_in)
    session.add(vin)
    session.commit()
    session.refresh(vin)
    return vin
