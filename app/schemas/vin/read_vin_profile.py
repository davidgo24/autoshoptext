from pydantic import BaseModel
from typing import Optional, List
from app.schemas.service_record.read_service_record import ServiceRecordRead

class VinProfileRead(BaseModel):
    id: int
    vin: str
    make: str
    model: str
    year: int
    trim: Optional[str] = None
    plate: Optional[str] = None
    service_records: List[ServiceRecordRead] = []

    class Config:
        orm_mode = True
