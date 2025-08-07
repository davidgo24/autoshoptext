from pydantic import BaseModel
from typing import Optional
from datetime import date

class ServiceRecordRead(BaseModel):
    id: int
    service_date: date
    oil_type: str
    oil_viscosity: str
    mileage_at_service: int
    next_service_mileage_due: int
    next_service_date_due: date
    notes: Optional[str] = None

    class Config:
        from_attributes = True
