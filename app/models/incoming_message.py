
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .contact import Contact

class IncomingMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    from_number: str = Field(index=True)
    to_number: str
    body: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    is_read: bool = Field(default=False, index=True)
    # cost_cents: int = Field(default=10) # Cost in cents for receiving message (e.g., 10 for $0.10) - Temporarily disabled

    contact_id: Optional[int] = Field(default=None, foreign_key="contact.id")
    contact: Optional["Contact"] = Relationship(back_populates="incoming_messages")
