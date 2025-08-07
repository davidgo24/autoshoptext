from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Contact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    phone_number: str = Field(unique=True, index=True)
    email: Optional[str] = Field(default=None, unique=True, index=True)

    # Many-to-many relationship with VIN
    vin_links: List["VINContactLink"] = Relationship(back_populates="contact")
    scheduled_messages: List["ScheduledMessage"] = Relationship(back_populates="contact")

from app.models.vin_contact_link import VINContactLink
from app.models.scheduled_message import ScheduledMessage
Contact.update_forward_refs()
VINContactLink.update_forward_refs()
ScheduledMessage.update_forward_refs()
