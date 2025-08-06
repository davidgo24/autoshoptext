from typing import Optional
from datetime import date
from sqlmodel import SQLModel, Field, Relationship

class ServiceRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vin_id: int = Field(foreign_key="vin.id")
    service_date: date = Field(default_factory=date.today)
    oil_type: str
    oil_viscosity: str
    mileage_at_service: int
    next_service_mileage_due: int
    next_service_date_due: date
    notes: Optional[str] = None

    vin: Optional["VIN"] = Relationship(back_populates="service_records")
