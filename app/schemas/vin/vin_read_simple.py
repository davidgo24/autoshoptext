from pydantic import BaseModel
from typing import Optional, List
from app.schemas.contact.contact import Contact

class VINReadSimple(BaseModel):
    id: int
    vin: str
    make: str
    model: str
    year: int
    trim: Optional[str] = None
    plate: Optional[str] = None
    contacts: List[Contact] = []

    class Config:
        from_attributes = True
