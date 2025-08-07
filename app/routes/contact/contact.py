from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.models.contact import Contact
from app.models.vin import VIN
from app.models.vin_contact_link import VINContactLink
from app.schemas.contact.contact import ContactCreate, ContactRead
from app.core.database import get_session

router = APIRouter()

@router.post("/", response_model=ContactRead)
async def create_contact(
    contact_in: ContactCreate, session: AsyncSession = Depends(get_session)
):
    # Check if contact with this phone number already exists
    existing_contact = await session.execute(
        select(Contact).where(Contact.phone_number == contact_in.phone_number)
    )
    if existing_contact.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Contact with this phone number already exists")

    contact = Contact.from_orm(contact_in)
    if contact.email == "":
        contact.email = None
    try:
        session.add(contact)
        await session.commit()
        await session.refresh(contact)
        return contact
    except IntegrityError as e:
        await session.rollback()
        if "ix_contact_phone_number" in str(e):
            raise HTTPException(status_code=400, detail="Contact with this phone number already exists.")
        elif "ix_contact_email" in str(e):
            raise HTTPException(status_code=400, detail="Contact with this email already exists.")
        else:
            raise HTTPException(status_code=500, detail="An unexpected database error occurred.")

@router.post("/{contact_id}/link_to_vin/{vin_id}")
async def link_contact_to_vin(
    contact_id: int, vin_id: int, session: AsyncSession = Depends(get_session)
):
    # Check if contact exists
    contact = await session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Check if VIN exists
    vin = await session.get(VIN, vin_id)
    if not vin:
        raise HTTPException(status_code=404, detail="VIN not found")

    # Check if link already exists
    existing_link = await session.execute(
        select(VINContactLink).where(
            (VINContactLink.contact_id == contact_id) &
            (VINContactLink.vin_id == vin_id)
        )
    )
    if existing_link.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Contact already linked to this VIN")

    vin_contact_link = VINContactLink(contact_id=contact_id, vin_id=vin_id)
    try:
        session.add(vin_contact_link)
        await session.commit()
        return {"message": "Contact linked to VIN successfully"}
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Contact is already linked to this VIN.")

@router.get("/vin/{vin_id}", response_model=list[ContactRead])
async def get_contacts_for_vin(
    vin_id: int, session: AsyncSession = Depends(get_session)
):
    vin = await session.get(VIN, vin_id)
    if not vin:
        raise HTTPException(status_code=404, detail="VIN not found")

    contacts = []
    for link in vin.contact_links:
        contacts.append(link.contact)
    return contacts

@router.get("/all", response_model=list[ContactRead])
async def get_all_contacts(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Contact))
    contacts = result.scalars().all()
    return contacts

@router.get("/search", response_model=list[ContactRead])
async def search_contacts(
    phone_number: str = Query(..., min_length=3), session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Contact).where(Contact.phone_number.like(f"%{phone_number}%"))
    )
    contacts = result.scalars().all()
    return contacts
