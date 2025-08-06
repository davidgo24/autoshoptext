from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.vin import VIN
from app.schemas.vin.create_new_vin import VinCreate
from app.core.database import get_session

router = APIRouter()

@router.post("/", response_model=VinCreate)
async def create_vin(
    vin_in: VinCreate, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(VIN).where(VIN.vin == vin_in.vin))
    vin_exists = result.scalar_one_or_none()
    
    if vin_exists:
        raise HTTPException(status_code=400, detail="VIN already exists")

    vin = VIN.from_orm(vin_in)
    session.add(vin)
    await session.commit()
    await session.refresh(vin)
    return vin
