from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class ScheduledMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    contact_id: int = Field(foreign_key="contact.id")
    vin_id: int = Field(foreign_key="vin.id")
    service_record_id: Optional[int] = Field(default=None, foreign_key="servicerecord.id", index=True)
    message_content: str
    scheduled_time: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    sent_at: Optional[datetime] = None
    status: str = Field(default="pending") # e.g., "pending", "sent", "canceled", "failed"
    is_reminder: bool = Field(default=False, index=True)
    # cost_cents: Optional[int] = Field(default=None) # Cost in cents when message is sent (e.g., 10 for $0.10) - Temporarily disabled

    contact: "Contact" = Relationship(back_populates="scheduled_messages")
    vin: "VIN" = Relationship(back_populates="scheduled_messages")

# Resolve forward references for type-annotated relationships
from app.models.contact import Contact
from app.models.vin import VIN
from app.models.service_record import ServiceRecord
ScheduledMessage.update_forward_refs()
Contact.update_forward_refs()
VIN.update_forward_refs()
ServiceRecord.update_forward_refs()