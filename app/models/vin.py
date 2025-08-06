from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class VIN(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vin: str = Field(index=True, unique=True, max_length=17)
    make: str
    model: str
    year: int
    trim: Optional[str] = None
    plate: Optional[str] = None

    service_records: List["ServiceRecord"] = Relationship(back_populates="vin")


from app.models.service_record import ServiceRecord
VIN.update_forward_refs()