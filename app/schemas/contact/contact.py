from pydantic import BaseModel
from typing import Optional

class ContactCreate(BaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None

class ContactRead(BaseModel):
    id: int
    name: str
    phone_number: str
    email: Optional[str] = None

    class Config:
        from_attributes = True
