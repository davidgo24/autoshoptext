from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.models.service_record import ServiceRecord
from app.models.vin import VIN
from app.models.contact import Contact
from app.models.vin_contact_link import VINContactLink
from app.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.service_record.read_service_record import ServiceRecordRead

from app.schemas.vin.vin_read_simple import VINReadSimple

router = APIRouter()

@router.get("/{service_record_id}", response_model=ServiceRecordRead)
async def get_service_record(service_record_id: int, session: AsyncSession = Depends(get_session)):
    """
    Fetches a single service record by its ID, including the full VIN object
    and all associated contacts.
    """
    result = await session.execute(
        select(ServiceRecord)
        .where(ServiceRecord.id == service_record_id)
        .options(
            selectinload(ServiceRecord.vin).options(
                selectinload(VIN.contact_links).options(
                    selectinload(VINContactLink.contact)
                )
            )
        )
    )
    service_record = result.scalars().first()

    if not service_record:
        raise HTTPException(status_code=404, detail="Service Record not found")

    vin_orm = service_record.vin
    print(f"DEBUG: vin_orm: {vin_orm}")
    print(f"DEBUG: vin_orm.contact_links: {vin_orm.contact_links}")
    contacts_for_vin_simple = []
    for link in vin_orm.contact_links:
        print(f"DEBUG: Processing link: {link}")
        print(f"DEBUG: link.contact: {link.contact}")
        if link.contact:
            contact_data = {
                "id": link.contact.id,
                "name": link.contact.name,
                "phone_number": link.contact.phone_number,
                "email": link.contact.email
            }
            contacts_for_vin_simple.append(Contact.model_validate(contact_data))
            print(f"DEBUG: Added contact to list: {link.contact.name}")
        else:
            print("DEBUG: link.contact is None or not loaded")
    print(f"DEBUG: Final contacts_for_vin_simple: {contacts_for_vin_simple}")

    vin_read_simple_instance = VINReadSimple(
        id=vin_orm.id,
        vin=vin_orm.vin,
        make=vin_orm.make,
        model=vin_orm.model,
        year=vin_orm.year,
        trim=vin_orm.trim,
        plate=vin_orm.plate,
        contacts=contacts_for_vin_simple # Explicitly pass contacts
    )

    service_record_read_instance = ServiceRecordRead(
        id=service_record.id,
        service_date=service_record.service_date,
        oil_type=service_record.oil_type,
        oil_viscosity=service_record.oil_viscosity,
        mileage_at_service=service_record.mileage_at_service,
        next_service_mileage_due=service_record.next_service_mileage_due,
        next_service_date_due=service_record.next_service_date_due,
        notes=service_record.notes,
        vin=vin_read_simple_instance # Pass the manually constructed VINReadSimple
    )

    return service_record_read_instance
