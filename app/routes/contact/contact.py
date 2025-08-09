from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from app.models.contact import Contact
from app.models.vin import VIN
from app.models.vin_contact_link import VINContactLink
from app.schemas.contact.contact import ContactCreate, Contact as ContactSchema
from app.core.database import get_session

router = APIRouter()

def normalize_phone_number(phone: str) -> str:
    """Normalize phone number to digits only, removing formatting"""
    # Remove all non-digit characters
    digits_only = ''.join(c for c in phone if c.isdigit())
    
    # Remove leading 1 if present (for US numbers)
    if len(digits_only) == 11 and digits_only.startswith('1'):
        digits_only = digits_only[1:]
    
    return digits_only

@router.post("/", response_model=ContactSchema)
async def create_contact(
    contact_in: ContactCreate, session: AsyncSession = Depends(get_session)
):
    # Normalize the phone number
    normalized_phone = normalize_phone_number(contact_in.phone_number)
    print(f"Attempting to create contact with phone number: {contact_in.phone_number} (normalized: {normalized_phone})")
    
    existing_contact_query = select(Contact).where(Contact.phone_number == normalized_phone)
    existing_contact_result = await session.execute(existing_contact_query)
    existing_contact_obj = existing_contact_result.scalar_one_or_none()

    if existing_contact_obj:
        print(f"Found existing contact with phone number: {existing_contact_obj.phone_number}")
        # Update the existing contact's name and email if provided
        # This allows "refreshing" contact info when someone re-adds with new details
        if contact_in.name != existing_contact_obj.name:
            existing_contact_obj.name = contact_in.name
        if contact_in.email and contact_in.email != "" and contact_in.email != existing_contact_obj.email:
            existing_contact_obj.email = contact_in.email
        
        await session.commit()
        await session.refresh(existing_contact_obj)
        return existing_contact_obj

    # Create new contact since none exists with this phone number
    contact = Contact.from_orm(contact_in)
    contact.phone_number = normalized_phone  # Store normalized version
    if contact.email == "":
        contact.email = None
    try:
        session.add(contact)
        await session.commit()
        await session.refresh(contact)
        return contact
    except IntegrityError as e:
        await session.rollback()
        # This should rarely happen now since we check for existing contacts
        if "ix_contact_phone_number" in str(e):
            # Try to fetch the contact that was created by another concurrent request
            retry_contact = await session.execute(existing_contact_query)
            found_contact = retry_contact.scalar_one_or_none()
            if found_contact:
                return found_contact
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

@router.get("/vin/{vin_id}", response_model=list[ContactSchema])
async def get_contacts_for_vin(
    vin_id: int, session: AsyncSession = Depends(get_session)
):
    # Load VIN with contact links and contacts
    result = await session.execute(
        select(VIN)
        .where(VIN.id == vin_id)
        .options(selectinload(VIN.contact_links).selectinload(VINContactLink.contact))
    )
    vin = result.scalar_one_or_none()
    
    if not vin:
        raise HTTPException(status_code=404, detail="VIN not found")

    contacts = []
    for link in vin.contact_links:
        if link.contact:  # Safety check
            contacts.append(link.contact)
    return contacts

@router.get("/all", response_model=list[ContactSchema])
async def get_all_contacts(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Contact))
    contacts = result.scalars().all()
    return contacts

@router.get("/search", response_model=list[ContactSchema])
async def search_contacts(
    phone_number: str = Query(..., min_length=3), session: AsyncSession = Depends(get_session)
):
    # Normalize the search term for better matching
    normalized_search = normalize_phone_number(phone_number)
    
    result = await session.execute(
        select(Contact).where(Contact.phone_number.like(f"%{normalized_search}%"))
    )
    contacts = result.scalars().all()
    return contacts
