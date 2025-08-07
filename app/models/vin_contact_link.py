from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class VINContactLink(SQLModel, table=True):
    vin_id: Optional[int] = Field(default=None, foreign_key="vin.id", primary_key=True)
    contact_id: Optional[int] = Field(default=None, foreign_key="contact.id", primary_key=True)

    vin: "VIN" = Relationship(back_populates="contact_links")
    contact: "Contact" = Relationship(back_populates="vin_links")
