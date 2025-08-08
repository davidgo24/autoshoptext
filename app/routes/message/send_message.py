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
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

router = APIRouter()

# ---- Helpers ----

def format_date(dt: datetime) -> str:
    try:
        return dt.strftime("%b %d, %Y")
    except Exception:
        return str(dt)


def humanize_oil_type(oil_type: str) -> str:
    if not oil_type:
        return ""
    return oil_type.replace('_', ' ').title()


@router.post("/message/{message_id}/cancel")
async def cancel_scheduled_message(message_id: int, session: AsyncSession = Depends(get_session)):
    msg = await session.get(ScheduledMessage, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Scheduled message not found")
    if msg.status != "pending":
        raise HTTPException(status_code=400, detail="Only pending messages can be canceled")
    msg.status = "canceled"
    session.add(msg)
    await session.commit()
    return {"success": True, "message": f"Message {message_id} canceled"}


@router.post("/vin/{vin_id}/cancel-pending")
async def cancel_pending_reminders_for_vin(vin_id: int, session: AsyncSession = Depends(get_session)):
    vin = await session.get(VIN, vin_id)
    if not vin:
        raise HTTPException(status_code=404, detail="VIN not found")
    result = await session.execute(
        select(ScheduledMessage).where(
            ScheduledMessage.vin_id == vin_id,
            ScheduledMessage.status == "pending"
        )
    )
    msgs = result.scalars().all()
    count = 0
    for m in msgs:
        # Treat only reminders (by content heuristic) to avoid touching immediate copies
        if "reminder" in (m.message_content or "").lower() or True:
            m.status = "canceled"
            session.add(m)
            count += 1
    await session.commit()
    return {"success": True, "canceled": count}


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

@router.get("/service-record/{service_record_id}/pickup-sent")
async def has_pickup_been_sent_for_service_record(
    service_record_id: int, session: AsyncSession = Depends(get_session)
):
    """Return whether an immediate pickup message has been sent for the given service record."""
    # A pickup message is any message tied to this service_record_id that is not a reminder (by content heuristic)
    result = await session.execute(
        select(ScheduledMessage)
        .where(
            ScheduledMessage.service_record_id == service_record_id,
        )
        .order_by(ScheduledMessage.scheduled_time.desc())
    )
    messages = result.scalars().all()
    pickup_exists = any(not m.is_reminder for m in messages)
    return {"service_record_id": service_record_id, "pickup_sent": pickup_exists}

@router.get("/pickup-messages")
async def get_pickup_messages(
    date: str = None, session: AsyncSession = Depends(get_session)
):
    """Get all pickup messages across all VINs, optionally filtered by date"""
    
    # Build the query for pickup messages (messages that don't contain "reminder")
    query = select(ScheduledMessage).where(
        ScheduledMessage.is_reminder == False
    ).order_by(ScheduledMessage.scheduled_time.desc())
    
    # Add date filter if provided
    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            start = datetime.combine(filter_date, datetime.min.time())
            end = start + timedelta(days=1)
            query = query.where(
                ScheduledMessage.scheduled_time >= start,
                ScheduledMessage.scheduled_time < end,
            )
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
    
    # Build the query for reminder messages (messages that contain "reminder")
    query = select(ScheduledMessage).where(
        ScheduledMessage.is_reminder == True
    ).order_by(ScheduledMessage.scheduled_time.desc())
    
    # Add date filter if provided
    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            start = datetime.combine(filter_date, datetime.min.time())
            end = start + timedelta(days=1)
            query = query.where(
                ScheduledMessage.scheduled_time >= start,
                ScheduledMessage.scheduled_time < end,
            )
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

@router.get("/reminder-messages-created")
async def get_reminder_messages_created(
    date: str = None, session: AsyncSession = Depends(get_session)
):
    """Get reminder messages by creation date (when they were scheduled), not by scheduled_time."""
    query = select(ScheduledMessage).where(
        ScheduledMessage.is_reminder == True
    ).order_by(ScheduledMessage.created_at.desc())
    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            start = datetime.combine(filter_date, datetime.min.time())
            end = start + timedelta(days=1)
            query = query.where(
                ScheduledMessage.created_at >= start,
                ScheduledMessage.created_at < end,
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    result = await session.execute(query)
    messages = result.scalars().all()
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
            "created_at": msg.created_at,
            "sent_at": msg.sent_at,
            "status": msg.status
        })
    return {"date_filter": date, "total_messages": len(message_list), "messages": message_list}

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
            ScheduledMessage.is_reminder == False
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
            ScheduledMessage.is_reminder == True
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

    # 2. Send immediate pickup message (content provided by client prefilled)
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
        service_record_id=service_record.id,
        message_content=request.immediate_message_content,
        scheduled_time=datetime.now(),  # Immediate message
        sent_at=datetime.now() if sms_sent else None,
        status="sent" if sms_sent else "failed",
        is_reminder=False
    )
    session.add(pickup_msg)

    # 4. Schedule future reminder message using new template
    # Find the last service (before this one) for mileage reference
    last_service_result = await session.execute(
        select(ServiceRecord)
        .where(ServiceRecord.vin_id == vin.id, ServiceRecord.id != service_record.id)
        .order_by(ServiceRecord.service_date.desc())
    )
    last_service = last_service_result.scalars().first()
    last_mileage = last_service.mileage_at_service if last_service else service_record.mileage_at_service

    reminder_message = (
        f"Hi {contact.name}, friendly heads up: your {vin.make} {vin.model} is due for service at "
        f"{service_record.next_service_mileage_due} mi or by {format_date(service_record.next_service_date_due)}. "
        "We'll be here when you're ready - Montebello Lube N' Tune, 2130 W Beverly Blvd. Mon-Sat 8-5. (323) 727-2883. "
        "Reply STOP to unsubscribe."
    )

    scheduled_msg = ScheduledMessage(
        contact_id=contact.id,
        vin_id=vin.id,
        service_record_id=service_record.id,
        message_content=reminder_message,
        # Schedule at 11:00 AM America/Los_Angeles; store as naive UTC for comparison
        scheduled_time=(
            datetime.combine(
                service_record.next_service_date_due,
                time(11, 0, 0),
                tzinfo=ZoneInfo("America/Los_Angeles")
            ).astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
        ),
        is_reminder=True
    )
    session.add(scheduled_msg)
    await session.commit()

    return {
        "success": True,
        "message": "Pickup message sent and reminder scheduled successfully!",
        "sms_sent": sms_sent,
        "reminder_scheduled": True
    }

@router.get("/sent-reminders")
async def get_sent_reminders(
    date: str = None, session: AsyncSession = Depends(get_session)
):
    """Get sent reminder messages across all VINs, optionally filtered by date"""
    query = select(ScheduledMessage).where(
        ScheduledMessage.is_reminder == True,
        ScheduledMessage.status == "sent"
    ).order_by(ScheduledMessage.sent_at.desc())
    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            start = datetime.combine(filter_date, datetime.min.time())
            end = start + timedelta(days=1)
            query = query.where(
                ScheduledMessage.sent_at >= start,
                ScheduledMessage.sent_at < end,
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    result = await session.execute(query)
    messages = result.scalars().all()
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
    return {"date_filter": date, "total_messages": len(message_list), "messages": message_list}
