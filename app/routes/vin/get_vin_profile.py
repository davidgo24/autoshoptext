from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.vin import VIN
from app.core.database import get_session  # provides AsyncSession

router = APIRouter()

@router.get("/{vin_or_last8}")
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
    query = query.options(selectinload(VIN.service_records))

    # Execute asynchronously
    result = await session.execute(query)
    vin = result.scalars().first()

    if not vin:
        raise HTTPException(status_code=404, detail="VIN not found")

    return vin
