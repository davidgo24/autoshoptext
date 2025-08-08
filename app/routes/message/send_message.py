from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.sms import send_sms
from app.models.service_record import ServiceRecord
from app.models.vin import VIN
from app.models.contact import Contact
from app.models.scheduled_message import ScheduledMessage
from app.schemas.message.send_message import SendMessageRequest
from datetime import datetime

router = APIRouter()

@router.get("/all-outbound")
async def get_all_outbound_messages(
    date: str = None, session: AsyncSession = Depends(get_session)
):
    """Get all outbound messages across all VINs, optionally filtered by date"""
    from datetime import datetime, date as date_type
    
    # Build the query
    query = select(ScheduledMessage).order_by(ScheduledMessage.scheduled_time.desc())
    
    # Add date filter if provided
    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.where(ScheduledMessage.scheduled_time >= filter_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    result = await session.execute(query)
    messages = result.scalars().all()

    # Format the response with contact and VIN details
    message_list = []
    for msg in messages:
        contact = await session.get(Contact, msg.contact_id)
        vin = await session.get(VIN, msg.vin_id)
        
        message_list.append({
            "id": msg.id,
            "contact_name": contact.name if contact else "Unknown",
            "contact_phone": contact.phone_number if contact else "Unknown",
            "vin_string": vin.vin if vin else "Unknown",
            "vehicle_info": f"{vin.year} {vin.make} {vin.model}" if vin else "Unknown",
            "message_content": msg.message_content,
            "scheduled_time": msg.scheduled_time,
            "sent_at": msg.sent_at,
            "status": msg.status,
            "is_reminder": "reminder" in msg.message_content.lower()
        })

    return {
        "date_filter": date,
        "total_messages": len(message_list),
        "messages": message_list
    }

@router.get("/pickup-messages")
async def get_pickup_messages(
    date: str = None, session: AsyncSession = Depends(get_session)
):
    """Get all pickup messages across all VINs, optionally filtered by date"""
    from datetime import datetime, date as date_type
    
    # Build the query for pickup messages (messages that don't contain "reminder")
    query = select(ScheduledMessage).where(
        ~ScheduledMessage.message_content.ilike("%reminder%")
    ).order_by(ScheduledMessage.scheduled_time.desc())
    
    # Add date filter if provided
    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.where(ScheduledMessage.scheduled_time >= filter_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    result = await session.execute(query)
    messages = result.scalars().all()

    # Format the response with contact and VIN details
    message_list = []
    for msg in messages:
        contact = await session.get(Contact, msg.contact_id)
        vin = await session.get(VIN, msg.vin_id)
        
        message_list.append({
            "id": msg.id,
            "contact_name": contact.name if contact else "Unknown",
            "contact_phone": contact.phone_number if contact else "Unknown",
            "vin_string": vin.vin if vin else "Unknown",
            "vehicle_info": f"{vin.year} {vin.make} {vin.model}" if vin else "Unknown",
            "message_content": msg.message_content,
            "scheduled_time": msg.scheduled_time,
            "sent_at": msg.sent_at,
            "status": msg.status
        })

    return {
        "date_filter": date,
        "total_messages": len(message_list),
        "messages": message_list
    }

@router.get("/reminder-messages")
async def get_reminder_messages(
    date: str = None, session: AsyncSession = Depends(get_session)
):
    """Get all reminder messages across all VINs, optionally filtered by date"""
    from datetime import datetime, date as date_type
    
    # Build the query for reminder messages (messages that contain "reminder")
    query = select(ScheduledMessage).where(
        ScheduledMessage.message_content.ilike("%reminder%")
    ).order_by(ScheduledMessage.scheduled_time.desc())
    
    # Add date filter if provided
    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.where(ScheduledMessage.scheduled_time >= filter_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    result = await session.execute(query)
    messages = result.scalars().all()

    # Format the response with contact and VIN details
    message_list = []
    for msg in messages:
        contact = await session.get(Contact, msg.contact_id)
        vin = await session.get(VIN, msg.vin_id)
        
        message_list.append({
            "id": msg.id,
            "contact_name": contact.name if contact else "Unknown",
            "contact_phone": contact.phone_number if contact else "Unknown",
            "vin_string": vin.vin if vin else "Unknown",
            "vehicle_info": f"{vin.year} {vin.make} {vin.model}" if vin else "Unknown",
            "message_content": msg.message_content,
            "scheduled_time": msg.scheduled_time,
            "sent_at": msg.sent_at,
            "status": msg.status
        })

    return {
        "date_filter": date,
        "total_messages": len(message_list),
        "messages": message_list
    }

@router.get("/vin/{vin_id}/history")
async def get_message_history_for_vin(
    vin_id: int, session: AsyncSession = Depends(get_session)
):
    """Get all message history for a specific VIN"""
    # Check if VIN exists
    vin = await session.get(VIN, vin_id)
    if not vin:
        raise HTTPException(status_code=404, detail="VIN not found")

    # Get all scheduled messages for this VIN
    result = await session.execute(
        select(ScheduledMessage)
        .where(ScheduledMessage.vin_id == vin_id)
        .order_by(ScheduledMessage.scheduled_time.desc())
    )
    messages = result.scalars().all()

    # Format the response
    message_history = []
    for msg in messages:
        contact = await session.get(Contact, msg.contact_id)
        message_history.append({
            "id": msg.id,
            "contact_name": contact.name if contact else "Unknown",
            "contact_phone": contact.phone_number if contact else "Unknown",
            "message_content": msg.message_content,
            "scheduled_time": msg.scheduled_time,
            "sent_at": msg.sent_at,
            "status": msg.status,
            "is_reminder": "reminder" in msg.message_content.lower()
        })

    return {
        "vin_id": vin_id,
        "vin_string": vin.vin,
        "vehicle_info": f"{vin.year} {vin.make} {vin.model}",
        "message_history": message_history
    }

@router.get("/vin/{vin_id}/pickup-history")
async def get_pickup_history_for_vin(
    vin_id: int, session: AsyncSession = Depends(get_session)
):
    """Get pickup message history for a specific VIN"""
    # Check if VIN exists
    vin = await session.get(VIN, vin_id)
    if not vin:
        raise HTTPException(status_code=404, detail="VIN not found")

    # Get pickup messages for this VIN (messages that don't contain "reminder")
    result = await session.execute(
        select(ScheduledMessage)
        .where(
            ScheduledMessage.vin_id == vin_id,
            ~ScheduledMessage.message_content.ilike("%reminder%")
        )
        .order_by(ScheduledMessage.scheduled_time.desc())
    )
    messages = result.scalars().all()

    # Format the response
    message_history = []
    for msg in messages:
        contact = await session.get(Contact, msg.contact_id)
        message_history.append({
            "id": msg.id,
            "contact_name": contact.name if contact else "Unknown",
            "contact_phone": contact.phone_number if contact else "Unknown",
            "message_content": msg.message_content,
            "scheduled_time": msg.scheduled_time,
            "sent_at": msg.sent_at,
            "status": msg.status
        })

    return {
        "vin_id": vin_id,
        "vin_string": vin.vin,
        "vehicle_info": f"{vin.year} {vin.make} {vin.model}",
        "pickup_history": message_history
    }

@router.get("/vin/{vin_id}/reminder-history")
async def get_reminder_history_for_vin(
    vin_id: int, session: AsyncSession = Depends(get_session)
):
    """Get reminder message history for a specific VIN"""
    # Check if VIN exists
    vin = await session.get(VIN, vin_id)
    if not vin:
        raise HTTPException(status_code=404, detail="VIN not found")

    # Get reminder messages for this VIN (messages that contain "reminder")
    result = await session.execute(
        select(ScheduledMessage)
        .where(
            ScheduledMessage.vin_id == vin_id,
            ScheduledMessage.message_content.ilike("%reminder%")
        )
        .order_by(ScheduledMessage.scheduled_time.desc())
    )
    messages = result.scalars().all()

    # Format the response
    message_history = []
    for msg in messages:
        contact = await session.get(Contact, msg.contact_id)
        message_history.append({
            "id": msg.id,
            "contact_name": contact.name if contact else "Unknown",
            "contact_phone": contact.phone_number if contact else "Unknown",
            "message_content": msg.message_content,
            "scheduled_time": msg.scheduled_time,
            "sent_at": msg.sent_at,
            "status": msg.status
        })

    return {
        "vin_id": vin_id,
        "vin_string": vin.vin,
        "vehicle_info": f"{vin.year} {vin.make} {vin.model}",
        "reminder_history": message_history
    }

@router.post("/send")
async def send_pickup_message(
    request: SendMessageRequest, session: AsyncSession = Depends(get_session)
):
    # 1. Fetch Service Record, VIN, and Contact
    service_record = await session.get(ServiceRecord, request.service_record_id)
    if not service_record:
        raise HTTPException(status_code=404, detail="Service Record not found")

    vin = await session.get(VIN, service_record.vin_id)
    if not vin:
        raise HTTPException(status_code=404, detail="VIN not found for service record")

    contact = await session.get(Contact, request.contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    # 2. Send immediate pickup message
    sms_sent = False
    if contact.phone_number:
        try:
            sms_result = await send_sms(contact.phone_number, request.immediate_message_content)
            sms_sent = sms_result is not None
        except Exception as e:
            print(f"Error sending SMS: {e}")
            # Continue with scheduling even if SMS fails

    # 3. Store the immediate pickup message in the database
    pickup_msg = ScheduledMessage(
        contact_id=contact.id,
        vin_id=vin.id,
        message_content=request.immediate_message_content,
        scheduled_time=datetime.now(),  # Immediate message
        sent_at=datetime.now() if sms_sent else None,
        status="sent" if sms_sent else "failed"
    )
    session.add(pickup_msg)

    # 4. Schedule future reminder message
    reminder_message_template = (
        "Reminder: Hi {name}, your {make} {model} ({vin_last_6}) is due for service on {next_date_due} or at {next_mileage_due} miles."
    )
    personalized_reminder_message = reminder_message_template.format(
        name=contact.name,
        make=vin.make,
        model=vin.model,
        vin_last_6=vin.vin[-6:],
        next_date_due=service_record.next_service_date_due.strftime("%Y-%m-%d"),
        next_mileage_due=service_record.next_service_mileage_due
    )

    scheduled_msg = ScheduledMessage(
        contact_id=contact.id,
        vin_id=vin.id,
        message_content=personalized_reminder_message,
        scheduled_time=datetime.combine(service_record.next_service_date_due, datetime.min.time())
    )
    session.add(scheduled_msg)
    await session.commit()

    return {
        "success": True,
        "message": "Pickup message sent and reminder scheduled successfully!",
        "sms_sent": sms_sent,
        "reminder_scheduled": True
    }
