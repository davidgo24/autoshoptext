from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class ScheduledMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    contact_id: int = Field(foreign_key="contact.id")
    vin_id: int = Field(foreign_key="vin.id")
    message_content: str
    scheduled_time: datetime
    sent_at: Optional[datetime] = None
    status: str = Field(default="pending") # e.g., "pending", "sent", "canceled", "failed"

    contact: "Contact" = Relationship(back_populates="scheduled_messages")
    vin: "VIN" = Relationship(back_populates="scheduled_messages")