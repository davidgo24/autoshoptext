from pydantic import BaseModel
from typing import Optional, List
from app.schemas.service_record.read_service_record import ServiceRecordRead
from app.schemas.contact.contact import ContactRead

class VinProfileRead(BaseModel):
    id: int
    vin: str
    make: str
    model: str
    year: int
    trim: Optional[str] = None
    plate: Optional[str] = None
    service_records: List[ServiceRecordRead] = []
    contacts: List[ContactRead] = []

    class Config:
        orm_mode = True
