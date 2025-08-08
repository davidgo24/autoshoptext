from pydantic import BaseModel
from typing import Optional

class ContactBase(BaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class Contact(ContactBase):
    id: int

    class Config:
        from_attributes = True
