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
    scheduled_messages: List["ScheduledMessage"] = Relationship(back_populates="vin")

    contact_links: List["VINContactLink"] = Relationship(back_populates="vin")

from app.models.service_record import ServiceRecord
from app.models.contact import Contact
from app.models.vin_contact_link import VINContactLink
from app.models.scheduled_message import ScheduledMessage
VIN.update_forward_refs()
Contact.update_forward_refs()
VINContactLink.update_forward_refs()
ScheduledMessage.update_forward_refs()