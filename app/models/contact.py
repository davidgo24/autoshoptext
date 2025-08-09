from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.vin_contact_link import VINContactLink
    from app.models.scheduled_message import ScheduledMessage
    from app.models.incoming_message import IncomingMessage

class Contact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    phone_number: str = Field(unique=True, index=True)
    email: Optional[str] = Field(default=None, unique=True, index=True)

    # Relationships
    vin_links: List["VINContactLink"] = Relationship(back_populates="contact")
    scheduled_messages: List["ScheduledMessage"] = Relationship(back_populates="contact")
    incoming_messages: List["IncomingMessage"] = Relationship(back_populates="contact")

# Update forward refs for all related models
from app.models.vin_contact_link import VINContactLink
from app.models.scheduled_message import ScheduledMessage
from app.models.incoming_message import IncomingMessage

Contact.update_forward_refs()
VINContactLink.update_forward_refs()
ScheduledMessage.update_forward_refs()
IncomingMessage.update_forward_refs()
